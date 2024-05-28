const JobProducer = require("../models/JobProducer.js");
const Job = require("../models/Job.js");

request = require("request");



//user에게 받은 java code 리팩토링 서버에 보내기
exports.sendToRefactoring = (req, res, next) => {
  const files = req.body.files;
  const numOfFiles = files.length;

  res.send("ok");
  //send to green server
  //    endpoint: /green_pattern
  //    data: javacode
  //    method: POST
  request.post(
    {
      headers: { "content-type": "application/json" },
      url: "http:/???/green_pattern",
      body: files,
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

exports.sendToMeasure = async (req, res, next) => {
  // id 발행해야 함
  const id = 1;
  const files = req.body.files;
  const numOfFiles = files.length;


  res.json({ job_id: "hi 영석~" });

  //각 파일마다 job 생성
  for (let i = 0; i < numOfFiles; i++) {
    let file = files[i].fileOriginB64Encoded;
    let path = files[i].fileRelativePath;

    //decode
    let code = Buffer.from(file, "base64").toString("utf-8");
    let job = new Job(id, code, path);
   
    JobProducer.updateDB(job);
    
    /*
    JobProducer.enqueue(job);
    JobProducer.updateStorage(job);
    */
  }
};
