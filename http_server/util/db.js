const firebase = require("firebase-admin");
const config = require("./config");

const db = firebase.initializeApp(config.firebaseConfig);

module.exports = db;
