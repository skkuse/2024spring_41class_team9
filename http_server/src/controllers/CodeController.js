request = require("request");
Job = require("../models/Job.js");
JobProducer = require("../models/JobProducer.js");

exports.send_to_refactoring = (req, res, next) => {
  //    endpoint: /green_pattern
  //    data: javacode
  //    method: POST
  const code = req.code; //디코딩 해야 함.
  const file = req.files[n].fileBinaryB64Encoded; //json 인터페이스 명확해지면 바꾸기
  console.log(file);

  //send to green server
  request.post(
    {
      headers: { "content-type": "application/json" },
      url: "",
      body: file,
      json: true,
    },
    (error, response, body) => {
      if (error) {
        return; //에러 코드 리턴
      }

      res.json(body); //user에게 리팩토링 결과 반환
    }
  );
};

exports.send_to_measure = (req, res, next) => {
  //const id =
  //const code = req. ..

  job = new Job(id, code);
  JobProducer.enqueue(job);
  JobProducer.update_db(job);
  JobProducer.update_storage(job);
};
