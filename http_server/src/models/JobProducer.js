const db = require('../../util/config');


class JobProducer {
  enqueue() {} //

  static updateDB(job) {
    //db.collection('jobs').doc(docId).set(job);
    db.ref('jobs').push({job_id:job.job_id ,path:job.path}, function(error){
      if(error)
        console.error(error)
      else
        console.log("success save !!");
    });
  }

  updateStorage(job) {
    try {
      const code = job.code;
    } catch (error) {}
  } //코드저장
}

module.exports = JobProducer;
