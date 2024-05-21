Job = require("../models/Job");
JobProducer = require("../models/JobProducer");

exports.send_to_refactoring = (req, res, next) => {};
//그냥 JobProducer를 Controller로 둘까
//Job 클래스에 enqueue update_db, update_storage 메소드를 두고
//Jobcontroller가 Job 생성하고 Job 클래스에 있는 메소드를 사용하는방식?

//이렇게 하면 모델끼리 서로 얽힌다.
exports.send_to_measure = (req, res, next) => {
  //const id =
  //const code = req. ..

  job = new Job(id, code);

  JobProducer.enqueue(Job);
  JobProducer.update_db(Job);
  JobProducer.update_storage(Job);
};
