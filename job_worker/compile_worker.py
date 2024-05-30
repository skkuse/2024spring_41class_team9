import os
from google.cloud import pubsub_v1
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
timeout = 5.0

# `projects/{project_id}/subscriptions/{subscription_id}`
subscription_path = subscriber.subscription_path(project_id, subscription_id)

# Firebase 설정
firebase_cred_path = 'swe-team9-5611bf21bb70.json'
firebase_cred = credentials.Certificate(firebase_cred_path)
firebase_admin.initialize_app(firebase_cred, {
    'databaseURL': 'https://swe-team9-default-rtdb.firebaseio.com'
})

# Realtime Database 연동
def realtime_db():
    ref = db.reference('jobs')
    snapshot = ref.get()# 데이터 읽기
    print(snapshot)

# Firestore 연동
def firestore_connect():
    # Firestore 클라이언트 초기화
    firestore_client = firestore.client()

    # 데이터 추가
    doc_ref = firestore_client.collection('---').document('---')
    doc_ref.set({
        '--': '--',
        '--': '--',
        '--': 00
    })

    # 데이터 읽기
    doc = doc_ref.get()
    if doc.exists:
        print(f'Document data: {doc.to_dict()}')
    else:
        print('No such document!')

def fetchJobMetadata():
    #job_id로 firestore에서 데이터 읽어오기 (code_path, binary_path, status)
    None

def runCompileJob(class_name):
    source_file_name = f"{class_name}.java"
    compile_command = f"javac {source_file_name}"
    result = subprocess.run(compile_command, shell=True, text=True, capture_output=True)
    if result.returncode == 0:
        print("Compilation successful.")
    else:
        print("Compilation failed.")
        print(result.stderr)
    
    return None

def saveCompileResult(class_name):
    #컴파일되어 현재 디렉토리에 만들어진 .class파일을 storage에 저장
    None

def measureJobPublish(project_id, topic_id):
    # project_id = "swe-team9"
    # topic_id = "measureTopic"
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)
    
    # data_str = f"Message number 1"
    # data = data_str.encode("utf-8")
    # future = publisher.publish(topic_path, data)
    # print(future.result())

    print(f"Published messages to {topic_path}.")


def subscribeAsync(message: pubsub_v1.subscriber.message.Message) -> None:
    print(f"Received message: {message.data}")

    realtime_db()
    #firestore_connect()

    # 1. message data에서 job_id알아내기
    # 2. fetchJobMetadata(job_id)
    # 3. runCompileJob(class_name)
    # 4. saveCompileResult(class_name)
    # 5. measureJobPublish("swe-team9", "measureTopic")

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
