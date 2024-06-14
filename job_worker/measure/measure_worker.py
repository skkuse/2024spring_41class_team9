import os
from google.api_core import retry
from google.cloud import pubsub_v1
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, firestore, db
import subprocess
import time
from system_values import get_system_values

# Pub/Sub 설정
pubsub_cred_path = 'pubsub-key.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = pubsub_cred_path
project_id = "swe-team9"
subscription_id = "measureTopic-sub"
PULL_DEADLINE = 300
NUM_MESSAGES = 1
TEMP_DIR = '/tmp'

# Firebase 설정
firebase_cred_path = 'firebase-key.json'
if not firebase_admin._apps:
    firebase_cred = credentials.Certificate(firebase_cred_path)
    firebase_admin.initialize_app(firebase_cred, {
        'databaseURL': 'https://swe-team9-default-rtdb.firebaseio.com'
    })

# Storage 설정
storage_cred_path = 'storage-key.json'
storage_client = storage.Client.from_service_account_json(storage_cred_path)

# Get system values
system_values = get_system_values()

def fetch_job_metadata(job_id):
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection('jobs').document(job_id)
    doc = doc_ref.get() 

    if doc.exists:
        job_data = doc.to_dict()
        doc_ref.update({'status': "MEASURING"})
        return job_data.get('binaryPath', None)
    else:
        print('No such document!')
        return None
        
def run_measure_job(binary_path):
    binary_path = binary_path+"/"

    bucket = storage_client.get_bucket('earth-saver')
    blobs = bucket.list_blobs(prefix=binary_path)

    file_list = []
    for blob in blobs:
        if blob.name.endswith('/'):
            continue
        file_list.append(blob.name)
    
    print("Files in directory:")
    for file in file_list:
        print(file)

    if len(file_list) == 1 and file_list[0].endswith('.class'):
        gcs_file_path = file_list[0]
        local_file_path = os.path.join(TEMP_DIR, os.path.basename(gcs_file_path))

        local_file_path = os.path.splitext(local_file_path)[0]

        blob = bucket.blob(gcs_file_path)
        blob.download_to_filename(local_file_path + ".class")
        print(f"Downloaded {gcs_file_path} to {local_file_path}.class")

        # 최대 30초 or 최대 10번
        start_time = time.time()
        result = subprocess.run(['java', '-cp', TEMP_DIR, os.path.relpath(local_file_path, TEMP_DIR)])
        end_time = time.time()

        if result.returncode != 0:
            print("Execution failed.")
            return False, result.stderr
        
        runtime = end_time - start_time
        max_runs = int(30/runtime) - 1

        run_count = min(max_runs, 9)

        for _ in range(run_count):
            start_time = time.time()
            subprocess.run(['java', '-cp', TEMP_DIR, os.path.relpath(local_file_path, TEMP_DIR)])
            end_time = time.time()
            runtime += end_time - start_time
        
        runtime_avg = runtime / (run_count+1)

        os.remove(local_file_path + ".class")

        if result.returncode == 0:
            print("Execution successful.")
            print(f"runtime: {runtime_avg} seconds")
            carbon_emission = cal_carbon_emission(runtime_avg)
            return True, carbon_emission
        else:
            print("Execution failed.")
            return False, result.stderr
    
    elif len(file_list) == 1 and file_list[0].endswith('.jar'):
        gcs_file_path = file_list[0]
        local_file_path = os.path.join(TEMP_DIR, os.path.basename(gcs_file_path))

        blob = bucket.blob(gcs_file_path)
        blob.download_to_filename(local_file_path)
        print(f"Downloaded {gcs_file_path} to {local_file_path}")

        start_time = time.time()
        result = subprocess.run(['java', '-jar', local_file_path])
        end_time = time.time()

        if result.returncode != 0:
            print("Execution failed.")
            return False, result.stderr

        runtime = end_time - start_time
        max_runs = int(30/runtime) - 1

        run_count = min(max_runs, 9)

        for _ in range(run_count):
            start_time = time.time()
            subprocess.run(['java', '-jar', local_file_path])
            end_time = time.time()
            runtime += end_time - start_time
        
        runtime_avg = runtime / (run_count+1)
        
        os.remove(local_file_path)

        if result.returncode == 0:
            print("Execution successful.")
            print(f"runtime: {runtime_avg} seconds")
            carbon_emission = cal_carbon_emission(runtime_avg)
            return True, carbon_emission
        else:
            print("Execution failed.")
            return False, result.stderr
    else:
        return False, "Not supported binary file"

def cal_carbon_emission(runtime):
    return (runtime * (system_values['core_num'] * system_values['core_power'] + system_values['mem_num'] * system_values['mem_power']) * system_values['PUE'] * 0.001) * system_values['CI']

def save_measure_result(carbon_emission, job_id):
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection('jobs').document(job_id)
    doc_ref.update({
        'carbonEmission': carbon_emission,
        'status': "DONE"
    })
    None

def process_message(job_id):
    binary_path = fetch_job_metadata(job_id)
    if binary_path:
        result = run_measure_job(binary_path)
        if result[0]:
            save_measure_result(result[1], job_id)
        return result
    else:
        return False, f"Job '{job_id}' doesn't exist"

def synchronous_pull() -> None:
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    with subscriber:
        while True:
            response = subscriber.pull(
                request={"subscription": subscription_path, "max_messages": NUM_MESSAGES},
                retry=retry.Retry(deadline=PULL_DEADLINE)
            )

            if not response.received_messages:
                print("No messages received.")
                time.sleep(1)
                continue

            job_id = response.received_messages[0].message.data.decode('utf-8')
            print(f"Job id: {job_id}")
            is_success, error_message = process_message(job_id)
            if is_success == False:
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
            print(f"Acknowledged message")
def main():
    synchronous_pull()

if __name__ == "__main__":
    main()