const express = require("express");
const router = express.Router();

const refactoring = require("../controllers/CodeController");

router.post("/refactoring_result", refactoring.send_to_refactoring);

module.exports = router;
