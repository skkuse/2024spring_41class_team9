const express = require('express');
const router = express.Router();


const code_controller = require('../controllers/CodeController');


router.post('/get_user_code',code_controller.get_code);

router.get('/status_request',);