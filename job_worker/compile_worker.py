import os
from google.cloud import pubsub_v1
from google.cloud import storage
from concurrent.futures import TimeoutError
import firebase_admin
from firebase_admin import credentials, firestore, db
import subprocess

# Pub/Sub 설정
pubsub_cred_path = 'swe-team9-ad44acd703b2.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = pubsub_cred_path
project_id = "swe-team9" # 프로젝트 이름
subscription_id = "compileTopic-sub" # 구독 이름
subscriber = pubsub_v1.SubscriberClient()
timeout = 30.0

# `projects/{project_id}/subscriptions/{subscription_id}`
subscription_path = subscriber.subscription_path(project_id, subscription_id)

# Firebase 설정
firebase_cred_path = 'swe-team9-5611bf21bb70.json'
if not firebase_admin._apps:
    firebase_cred = credentials.Certificate(firebase_cred_path)
    firebase_admin.initialize_app(firebase_cred, {
        'databaseURL': 'https://swe-team9-default-rtdb.firebaseio.com'
    })

# Storage 설정
storage_cred_path = 'swe-team9-feea36c92e8c.json'
storage_client = storage.Client.from_service_account_json(storage_cred_path)


def fetchJobMetadata(job_id):
    #job_id로 firestore에서 데이터 읽어오기 (code_path, binary_path, status)
    firestore_client = firestore.client()
    # jobs 컬렉션에서 job_id 문서 참조
    doc_ref = firestore_client.collection('jobs').document(job_id)
    # 문서 가져오기
    doc = doc_ref.get() 
    if doc.exists:
        job_data = doc.to_dict()
        code_path = job_data.get('codePath', None)
        binary_path = job_data.get('binaryPath', None)

        doc_ref.update({
            'status': "COMPILING"
        })
        
        return {
            "code_path": code_path,
            "binary_path": binary_path
        }
    else:
        print('No such document!')
        return None

def runCompileJob(code_path, binary_path):
    code_path = code_path+"/"
    print(code_path)

    bucket = storage_client.get_bucket('earth-saver')
    blobs = bucket.list_blobs(prefix=code_path)

    file_list = []
    for blob in blobs:
        if blob.name.endswith('/'):
            continue
        file_list.append(blob.name)
    print("Files in directory:")
    for file in file_list:
        print(file)
    
    if len(file_list) == 1 and file_list[0].endswith('.java'): #single source code
        # Download project to local storage
        gcs_file_path = file_list[0]
        local_file_path = os.path.basename(gcs_file_path)

        blob = bucket.blob(gcs_file_path)
        blob.download_to_filename(local_file_path)
        print(f"Downloaded {gcs_file_path} to {local_file_path}")

        # Compile
        compile_command = f"javac {local_file_path}"
        result = subprocess.run(compile_command, shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            print("Compilation successful.")
        else:
            print("Compilation failed.")
            print(result.stderr)
        
        class_file_path = local_file_path.replace('.java', '.class')
        upload_path = binary_path + '/' + os.path.basename(class_file_path)
        print(class_file_path)
        print(upload_path)
        saveCompileResult(class_file_path, upload_path)
    else: # Java project
        print("project")

        # Download project to local storage
        for gcs_file_path in file_list:
            local_file_path = 'code/' + gcs_file_path[len(code_path):]
            local_directory = os.path.dirname(local_file_path)
            if not os.path.exists(local_directory):
                os.makedirs(local_directory)  # Ensure directory exists
            blob = bucket.blob(gcs_file_path)
            blob.download_to_filename(local_file_path)
            print(f"Downloaded {gcs_file_path} to {local_file_path}")

        # Modify build.gradle to make the JAR runnable
        gradle_file = os.path.join('code','app', 'build.gradle')
        with open(gradle_file, 'a') as file:
            file.write('\njar {\n')
            file.write('    manifest {\n')
            file.write('        attributes("Main-Class": "demo.App")\n')
            file.write('    }\n')
            file.write('    from {\n')
            file.write('        configurations.runtimeClasspath.collect { it.isDirectory() ? it : zipTree(it) }\n')
            file.write('    }\n')
            file.write('}\n')

        # Use Gradle to build the project
        print("Building project with Gradle...")
        subprocess.run(['C:\\Gradle\\gradle-8.8\\bin\\gradle.bat', 'jar'], cwd=os.path.join('code', 'app'))
        
        # Upload the jar file
        source_folder = os.path.join('code','app', 'build', 'libs')
        for file_name in os.listdir(source_folder):
            if file_name.endswith('.jar'):
                jar_file_path = 'code/app/build/libs/' + file_name
                upload_path = binary_path + '/' + file_name
                print(jar_file_path)
                print(upload_path)
                saveCompileResult(jar_file_path, upload_path)

    return None

def saveCompileResult(binary_file_path, upload_path):
    # Save binary files to storage
    bucket = storage_client.get_bucket('earth-saver')
    blob = bucket.blob(upload_path)
    blob.upload_from_filename(binary_file_path)
    print(f"Uploaded {binary_file_path} to gs://earth-saver/{upload_path}")


def measureJobPublish(project_id, topic_id, job_id):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    data = job_id.encode("utf-8")
    try:
        future = publisher.publish(topic_path, data)
        message_id = future.result()
        print(f"Message published successfully with ID: {message_id}")
        # status update
        firestore_client = firestore.client()
        doc_ref = firestore_client.collection('jobs').document(job_id)
        doc_ref.update({
            'status': "MEASURE_ENQUEUED"
        })
    except Exception as e:
        print(f"An error occurred: {e}")


def subscribeAsync(message: pubsub_v1.subscriber.message.Message) -> None:
    # 1. message data에서 job_id알아내기
    job_id = message.data.decode('utf-8') 
    print(f"Job id: {job_id}")

    # 2. fetchJobMetadata(job_id) + status update to "COMPILING"
    job_metadata = fetchJobMetadata(job_id)
    if job_metadata:
        code_path = job_metadata.get('code_path')
        binary_path = job_metadata.get('binary_path')

        # 3. Run compile job and save the result
        runCompileJob(code_path, binary_path)

        # 4. Measure job publish + status update to "MEASURE_ENQUEUED"
        measureJobPublish("swe-team9", "measureTopic", job_id)
    
    print("ack")
    message.ack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=subscribeAsync)
print(f"Listening for messages on {subscription_path}..\n")

# Wrap subscriber in a 'with' block to automatically call close() when done.
with subscriber:
    try:
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        streaming_pull_future.result(timeout=timeout)
    except TimeoutError:
        streaming_pull_future.cancel()  # Trigger the shutdown.
        streaming_pull_future.result()  # Block until the shutdown is complete.
