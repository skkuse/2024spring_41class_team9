const https = require('https')
const express = require('express')
const app = express();

//TODO: firebase 연동 ,job producer에서 id발행 
const web_router = require('./routes/Web');
const cli_router = require('./routes/Web');

//Web App
app.use('/web',web_router);

//CLI App
app.use('/cli',cli_router);

//Green Pattern Refactoring Server

//run
app.listen(3000, ()=> {
    console.log('running http server');
});

