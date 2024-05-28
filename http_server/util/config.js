const firebase = require('firebase');

const firebaseConfig = {
  apiKey: "AIzaSyDLNw0TqgL2FKUZVIkKtdNZzn2QxNAstww",
  authDomain: "test1-c3289.firebaseapp.com",
  projectId: "test1-c3289",
  storageBucket: "test1-c3289.appspot.com",
  messagingSenderId: "545444248558",
  appId: "1:545444248558:web:a44ed4902688382b0d6cff",
  measurementId: "G-VLBEM32M74"
};

firebase.initializeApp(firebaseConfig)
let db = firebase.database();

module.exports = db;