const firebase = require("../../util/db");
const firestore = firebase.firestore();

class JobProducer {
  enqueue() {} //

  updateDB(job) {
    try {
      const path = job.path;
      return firestore.collection(); //firebase에 코드 path저장
    } catch (error) {}
  }

  updateStorage(job) {
    try {
      const code = job.code;
    } catch (error) {}
  } //코드저장
}

module.exports = JobProducer;
