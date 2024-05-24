const express = require("express");
const router = express.Router();

const user = require("../controllers/CodeController");

router.post("/refactoring_code", user.send_to_refactoring);

router.post("/measure_carbonEmission", user.send_to_measure);

module.exports = router;
