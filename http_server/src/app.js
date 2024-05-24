const https = require("https");
const path = require("path");
const express = require("express");

const app = express();

//TODO:job producer에서 id발행, firebase 연동
const user_router = require("./routes/User");
const refactoring_router = require("./routes/Refactoring");

//Web App and CLI App (user)
app.use("/user", user_router);

//Refactoring server
app.use("/refactoring", refactoring_router);

//run
app.listen(3000, () => {
  console.log("running http server");
});
