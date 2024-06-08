import os
from google.api_core import retry
from google.cloud import pubsub_v1
from google.cloud import storage
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import firebase_admin
from firebase_admin import credentials, firestore, db
import subprocess
import time
from system_values import get_system_values

# Pub/Sub 설정
pubsub_cred_path = 'swe-team9-ad44acd703b2.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = pubsub_cred_path
project_id = "swe-team9" # 프로젝트 이름
subscription_id = "measureTopic-sub" # 구독 이름
subscriber = pubsub_v1.SubscriberClient()
PULL_DEADLINE = 300
TIMEOUT = 30.0
NUM_MESSAGES = 1

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

# Get system values
system_values = get_system_values()

def fetch_job_metadata(job_id):
    #job_id로 firestore에서 데이터 읽어오기 (binary_path)
    firestore_client = firestore.client()
    # jobs 컬렉션에서 job_id 문서 참조
    doc_ref = firestore_client.collection('jobs').document(job_id)
    # 문서 가져오기
    doc = doc_ref.get() 
    if doc.exists:
        job_data = doc.to_dict()
        binary_path = job_data.get('binaryPath', None)

        doc_ref.update({
            'status': "MEASURING"
        })
        
        return binary_path
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
        local_file_path = os.path.basename(gcs_file_path)

        # 확장자 제거
        local_file_path = os.path.splitext(local_file_path)[0]

        # Google Cloud Storage에서 파일 다운로드
        blob = bucket.blob(gcs_file_path)
        blob.download_to_filename(local_file_path + ".class")
        print(f"Downloaded {gcs_file_path} to {local_file_path}.class")      

        start_time = time.time()
        result = subprocess.run(['java', local_file_path])
        end_time = time.time()
        runtime = end_time - start_time

        print(f"runtime: {runtime} seconds")
        if result.returncode == 0:
            print("Execution successful.")
        else:
            print("Execution failed.")

        os.remove(local_file_path + ".class")

        return runtime
    
    elif len(file_list) == 1 and file_list[0].endswith('.jar'):
        gcs_file_path = file_list[0]
        local_file_path = os.path.basename(gcs_file_path)

        blob = bucket.blob(gcs_file_path)
        blob.download_to_filename(local_file_path)
        print(f"Downloaded {gcs_file_path} to {local_file_path}")
        
        # Run the generated JAR file
        start_time = time.time()
        result = subprocess.run(['java', '-jar', local_file_path])
        end_time = time.time()
        runtime = end_time - start_time
        print(f"runtime: {runtime} seconds")

        if result.returncode == 0:
            print("Execution successful.")
        else:
            print("Execution failed.")

        os.remove(local_file_path)
        
        return runtime

    else:
        print(f"binary file error\n")

def cal_carbon_emission(runtime):
    return (runtime * (system_values['core_num'] * system_values['core_power'] + system_values['mem_num'] * system_values['mem_power']) * system_values['PUE'] * 0.001) * system_values['CI']

def save_measure_result(carbon_emission, job_id):
    # DB update
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection('jobs').document(job_id)
    doc_ref.update({
        'carbonEmission': carbon_emission,
        'status': "DONE"
    })
    None

def process_message(received_message):
    # 1. message data에서 job_id알아내기
    job_id = received_message.message.data.decode('utf-8')
    print(f"Job id: {job_id}")
    # 2. binary_path = fetch_job_metadata(job_id)
    binary_path = fetch_job_metadata(job_id)
    if binary_path:
        # 3. carbon_emission = run_measure_job(binary_path)
        runtime = run_measure_job(binary_path)
        carbon_emission = cal_carbon_emission(runtime)

        # 4. save_measure_result(carbon_emission)
        save_measure_result(carbon_emission, job_id)
    return received_message.ack_id

def synchronous_pull() -> None:
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    with subscriber:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": NUM_MESSAGES},
            retry=retry.Retry(deadline=PULL_DEADLINE)
        )

        if not response.received_messages:
            print("No messages received.")
            return

        # Execute processing of messages in a thread pool
        with ThreadPoolExecutor(max_workers=NUM_MESSAGES) as executor:
            future = executor.submit(process_message, response.received_messages[0])
            try:
                # Wait for the message to be processed within the timeout period
                future.result(timeout=TIMEOUT)
            except TimeoutError:
                print("Processing timed out. Message will not be acknowledged and will be re-delivered.")
                return  # Exit the function without acknowledging the message

        # Acknowledge all successfully processed messages
        ack_id = response.received_messages[0].ack_id
        subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": [ack_id]})
        print(f"Acknowledged message")

def main():
    synchronous_pull()

if __name__ == "__main__":
    main()