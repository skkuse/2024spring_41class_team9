const db = require("../../util/database");
const { Storage } = require("@google-cloud/storage");
const { PubSub } = require("@google-cloud/pubsub");

class JobProducer {
  static async enqueue(job) {
    //create client
    const job_id = job.job_id;
    const projectId = "swe-team9";
    const pubSubClient = new PubSub({
      projectId: projectId,
      credentials: {
        client_email: process.env.GOOGLE_PUBSUB_EMAIL,
        private_key: process.env.GOOGLE_APPLICATION_CREDENTIALS,
      },
    });
    const data = job_id;
    const dataBuffer = Buffer.from(data);
    const topicId = "compileTopic";
    const topicNameOrId = `projects/swe-team9/topics/${topicId}`;
    try {
      const messageId = await pubSubClient
        .topic(topicNameOrId)
        .publishMessage({ data: dataBuffer });

      console.log(`Message ${messageId} published.`);
    } catch (error) {
      console.log(`Received error while publishing: ${error.message}`);
    }
    db.collection("jobs").doc(job_id).update({ status: "COMPILE_ENQUEUED" });
  }

  static async updateDB(job) {
    let newDoc = db.collection("jobs").doc();
    let job_id = newDoc.id;
    job.job_id = job_id;

    let currentPathValues = `jobs/${job_id}/code`;
    let binaryPath = `jobs/${job_id}/binary`;

    await newDoc.set({
      codePath: currentPathValues,
      binaryPath: binaryPath,
      carbonEmission: 0,
      status: "--",
    });
    console.log(`${job_id} uploaded to firestore`);
    return;
  }

  static async updateStorage(job) {
    const fileName = job.path;

    const storage = new Storage({
      projectId: process.env.GCLOUD_PROJECT_ID,

      credentials: {
        client_email: process.env.GCLOUD_CLIENT_EMAIL,
        private_key: process.env.GCLOUD_PRIVATE_KEY.replace(/\\n/g, "\n"),
      },
    });

    try {
      const bucket = storage.bucket("earth-saver");
      const codeFile = bucket.file(`jobs/${job.job_id}/code/${job.path}`);
      const codeBuffer = Buffer.from(job.code, "utf-8");

      //스토리지에 코드 파일 업로드
      await codeFile.save(codeBuffer, {
        contentType: "application/plain",
      });
    } catch (error) {
      console.log(error);
    }
    console.log(`${job.job_id} uploaded to storage`);
  }
}

module.exports = JobProducer;
