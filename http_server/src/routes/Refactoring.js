const express = require("express");
const router = express.Router();

const refactoring = require("../controllers/CodeController");

router.post("/refactoring_result", refactoring.get_refactoring_code);

module.exports = router;
