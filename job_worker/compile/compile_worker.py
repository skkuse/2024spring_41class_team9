import os
import logging
from google.api_core import retry
from google.cloud import pubsub_v1
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, firestore
import subprocess
import shutil
import time
from constant import PROJECT_ID, COMPILE_SUBSCRIPTION_ID, FIREBASE_DB_URL, STORAGE_BUCKET_NAME

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# constants
PULL_DEADLINE = 5
TIMEOUT = 30.0
NUM_MESSAGES = 1
TEMP_DIR = '/tmp'

# Pub/Sub 설정
pubsub_cred_path = 'pubsub-key.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = pubsub_cred_path

# Firebase 설정
firebase_cred_path = 'firebase-key.json'
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_cred_path)
    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})

# Storage 설정
storage_cred_path = 'storage-key.json'
storage_client = storage.Client.from_service_account_json(storage_cred_path)


def fetch_job_metadata(job_id):
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection('jobs').document(job_id)
    doc = doc_ref.get()

    if doc.exists:
        job_data = doc.to_dict()
        doc_ref.update({'status': "COMPILING"})
        return job_data.get('codePath', None), job_data.get('binaryPath', None)
    
    logging.error('No such document!')
    return None, None

def run_compile_job(code_path, binary_path):
    code_path = code_path+"/"

    bucket = storage_client.get_bucket(STORAGE_BUCKET_NAME)
    blobs = bucket.list_blobs(prefix=code_path)

    file_list = []
    for blob in blobs:
        if blob.name.endswith('/'):
            continue
        file_list.append(blob.name)
    
    logging.info("Files in directory:")
    for file in file_list:
        logging.info(file)
    
    if len(file_list) == 1 and file_list[0].endswith('.java'): #single source code
        # Download project to local storage
        gcs_file_path = file_list[0]
        local_file_path =  os.path.join(TEMP_DIR, os.path.basename(gcs_file_path))

        blob = bucket.blob(gcs_file_path)
        blob.download_to_filename(local_file_path)
        logging.info(f"Downloaded {gcs_file_path} to {local_file_path}")

        # Compile
        compile_command = f"javac {local_file_path}"
        result = subprocess.run(compile_command, shell=True, text=True, capture_output=True)

        os.remove(local_file_path)
        if result.returncode == 0:
            logging.info("Compilation successful.")
        else:
            logging.error("Compilation failed.")
            logging.error(result.stderr)
            return False, result.stderr
        
        class_file_path = local_file_path.replace('.java', '.class')
        upload_path = binary_path + '/' + os.path.basename(class_file_path)
        logging.info(f"Class file path: {class_file_path}")
        logging.info(f"Upload path: {upload_path}")
        save_compile_result(class_file_path, upload_path)
    else: # Java project
        #print("project")
        # Download project to local storage
        for gcs_file_path in file_list:
            local_file_path = TEMP_DIR +'/code/' + gcs_file_path[len(code_path):]
            local_directory = os.path.dirname(local_file_path)
            if not os.path.exists(local_directory):
                os.makedirs(local_directory)  # Ensure directory exists
            blob = bucket.blob(gcs_file_path)
            blob.download_to_filename(local_file_path)
            logging.info(f"Downloaded {gcs_file_path} to {local_file_path}")

        # Modify build.gradle to make the JAR runnable
        gradle_file = os.path.join(TEMP_DIR,'code','app', 'build.gradle')
        try:
            with open(gradle_file, 'a') as file:
                file.write('\njar {\n')
                file.write('    manifest {\n')
                file.write('        attributes \'Main-Class\': application.mainClass\n')
                file.write('    }\n')
                file.write('    from {\n')
                file.write('        configurations.runtimeClasspath.collect { it.isDirectory() ? it : zipTree(it) }\n')
                file.write('    }\n')
                file.write('}\n')
        except Exception as e:
            logging.error(f"Error updating build.gradle: {e}")
            return False, str(e)

        # Use Gradle to build the project
        logging.info("Building project with Gradle...")
        try:
            gradle_path = '/opt/gradle/gradle-8.8/bin/gradle'
            gradle_cache_dir = os.path.join(TEMP_DIR, 'code', '.gradle')
            if os.path.exists(gradle_cache_dir):
                shutil.rmtree(gradle_cache_dir)
                logging.info("Deleted gradle cache")
            result = subprocess.run([gradle_path, 'jar'], cwd=os.path.join(TEMP_DIR, 'code', 'app'))
        except Exception as e:
            logging.error(str(e))
            return False, str(e)

        if result.returncode == 0:
            logging.info("Compilation successful.")
            # Upload the jar file
            source_folder = os.path.join(TEMP_DIR, 'code','app', 'build', 'libs')
            for file_name in os.listdir(source_folder):
                if file_name.endswith('.jar'):
                    jar_file_path = '/tmp/code/app/build/libs/' + file_name
                    upload_path = binary_path + '/' + file_name
                    logging.info(jar_file_path)
                    logging.info(upload_path)
                    save_compile_result(jar_file_path, upload_path)
            code_directory = os.path.join(TEMP_DIR, 'code')
            if os.path.exists(code_directory):
                shutil.rmtree(code_directory)
                logging.info("Deleted 'code' directory")
        else:
            code_directory = os.path.join(TEMP_DIR, 'code')
            if os.path.exists(code_directory):
                shutil.rmtree(code_directory)
                logging.info("Deleted 'code' directory")
            logging.error("Compilation failed.")
            logging.error(result.stderr)
            return False, result.stderr

    return True, None

def save_compile_result(binary_file_path, upload_path):
    # Save binary files to storage
    bucket = storage_client.get_bucket(STORAGE_BUCKET_NAME)
    blob = bucket.blob(upload_path)
    blob.upload_from_filename(binary_file_path)
    logging.info(f"Uploaded {binary_file_path} to gs://{STORAGE_BUCKET_NAME}/{upload_path}")
    os.remove(binary_file_path)

def measure_job_publish(job_id):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, "measureTopic")

    data = job_id.encode("utf-8")
    try:
        future = publisher.publish(topic_path, data)
        message_id = future.result()
        logging.info(f"Message published successfully with ID: {message_id}")
        firestore_client = firestore.client()
        doc_ref = firestore_client.collection('jobs').document(job_id)
        doc_ref.update({
            'status': "MEASURE_ENQUEUED"
        })
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def process_message(job_id):
    code_path, binary_path = fetch_job_metadata(job_id)
    if code_path and binary_path:
        result = run_compile_job(code_path, binary_path)
        return result
    else:
        return False, f"Job '{job_id}' doesn't exist"

def synchronous_pull() -> None:
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, COMPILE_SUBSCRIPTION_ID)

    with subscriber:
        while True:
            response = subscriber.pull(
                request={"subscription": subscription_path, "max_messages": NUM_MESSAGES},
                retry=retry.Retry(deadline=PULL_DEADLINE)
            )

            if not response.received_messages:
                logging.info("No messages received.")
                time.sleep(1)
                continue
            
            job_id = response.received_messages[0].message.data.decode('utf-8')
            logging.info(f"Job id: {job_id}")

            is_success, error_message = process_message(job_id)
            if is_success:
                measure_job_publish(job_id)
            else:
                firestore_client = firestore.client()
                doc_ref = firestore_client.collection('jobs').document(job_id)
                doc = doc_ref.get()
                if doc.exists:
                    doc_ref.update({
                        'status': "ERROR",
                        'error': error_message
                    })
            
            ack_id = response.received_messages[0].ack_id
            subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": [ack_id]})
            logging.info("Acknowledged message")

def main():
    synchronous_pull()

if __name__ == "__main__":
    main()