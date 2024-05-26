const express = require("express");
const router = express.Router();

const user = require("../controllers/CodeController");

router.post("/refactoring_code", user.sendToRefactoring);

router.post("/measure_carbonEmission", user.sendToMeasure);

module.exports = router;
