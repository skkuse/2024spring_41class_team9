import os
from google.cloud import pubsub_v1


pubsub_cred_path = 'pubsub-key.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = pubsub_cred_path

project_id = "swe-team9"
topic_id = "compileTopic"
publisher = pubsub_v1.PublisherClient()
# The `topic_path` method creates a fully qualified identifier
# in the form `projects/{project_id}/topics/{topic_id}`
topic_path = publisher.topic_path(project_id, topic_id)

#u9kCUxuNYwoiOkjhg6S3
# KdnypfjrBHrv44mErYYU
# 0ngmCsUk5fA7CGUydLEa
data_str = f"KdnypfjrBHrv44mErYYU"
data = data_str.encode("utf-8")
future = publisher.publish(topic_path, data)
print(future.result())

print(f"Published messages to {topic_path}.")