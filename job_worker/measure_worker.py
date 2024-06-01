import os
from google.cloud import pubsub_v1
from concurrent.futures import TimeoutError
import firebase_admin
from firebase_admin import credentials, firestore, db
import subprocess
import psutil
import time

# Pub/Sub 설정
pubsub_cred_path = 'swe-team9-ad44acd703b2.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = pubsub_cred_path
project_id = "swe-team9" # 프로젝트 이름
subscription_id = "measureTopic-sub" # 구독 이름
subscriber = pubsub_v1.SubscriberClient()
timeout = 5.0

# `projects/{project_id}/subscriptions/{subscription_id}`
subscription_path = subscriber.subscription_path(project_id, subscription_id)

# Firebase 설정
firebase_cred_path = 'swe-team9-5611bf21bb70.json'
firebase_cred = credentials.Certificate(firebase_cred_path)
firebase_admin.initialize_app(firebase_cred, {
    'databaseURL': 'https://swe-team9-default-rtdb.firebaseio.com'
})

def fetchJobMetadata(job_id):
    #job_id로 firestore에서 데이터 읽어오기 (code_path, binary_path, status)
    None


def runMeasureJob(binary_path):
    command = ["java", binary_path]

    process = psutil.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    SLEEP_SECONDS = 0.1 # Sleep time in seconds between CPU and memory checks. Lower values will increase CPU usage then effect the monitoring result.

    max_memory = 0
    max_cpu = 0
    start_time = time.time()

    try:
        while process.is_running():
            current_memory = process.memory_info().rss
            if current_memory > max_memory:
                max_memory = current_memory
            
            # 전체 실행 시간 동안의 평균 CPU 사용량
            # current_cpu = process.cpu_percent(interval=None) / psutil.cpu_count()

            current_cpu = process.cpu_percent(interval=0.1) # 순간적인 최대 CPU 사용량
            if current_cpu > max_cpu:
                max_cpu = current_cpu
            
            time.sleep(SLEEP_SECONDS) # Sleep for a short period to avoid high CPU usage

    except psutil.NoSuchProcess:
        pass
    except psutil.AccessDenied:
        print("Access Denied to process information")
    except Exception as e:
        print(f"An error occurred: {e}")

    end_time = time.time()
    runtime = end_time - start_time

    # max_memory, max_cpu, runtime으로 carbon_emission 계산하기
    carbon_emission = 0
    return carbon_emission

def saveMeasureResult(carbonEmission):
    None

def subscribeAsync(message: pubsub_v1.subscriber.message.Message) -> None:
    print(f"Received message: {message.data}")
    # 1. message data에서 job_id알아내기
    # 2. binary_path = fetchJobMetadata(job_id)
    # 3. carbon_emission = runMeasureJob(binary_path)
    # 4. saveMeasureResult(carbon_emission)

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
