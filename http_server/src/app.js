const https = require('https')
const express = require('express')
const app = express();

//TODO:job producer에서 id발행 
const user_router = require('./routes/User');



//Web App and CLI App (user)
app.use('/user',user_router);



//run
app.listen(3000, ()=> {
    console.log('running http server');
});

