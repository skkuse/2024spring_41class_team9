const express = require("express");
const router = express.Router();

const user = require("../controllers/CodeController");

// add option method for CORS
router.options("/refactoring_code", (req, res) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Methods", "POST");
  res.header("Access-Control-Allow-Headers", "Content-Type");
  res.header("Access-Control-Max-Age", "3600");
  res.send();
});

router.options("/measure_carbonEmission", (req, res) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Methods", "POST");
  res.header("Access-Control-Allow-Headers", "Content-Type");
  res.header("Access-Control-Max-Age", "3600");
  res.send();
});

router.post("/refactoring_code", user.sendToRefactoring);

router.post("/measure_carbonEmission", user.sendToMeasure);

module.exports = router;
