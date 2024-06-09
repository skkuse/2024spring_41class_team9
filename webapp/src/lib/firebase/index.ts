// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBUid7bytdJumdUGK6OmHdqpv3bMzksfSk",
  authDomain: "swe-team9.firebaseapp.com",
  databaseURL: "https://swe-team9-default-rtdb.firebaseio.com",
  projectId: "swe-team9",
  storageBucket: "swe-team9.appspot.com",
  messagingSenderId: "99707147898",
  appId: "1:99707147898:web:94384bd5f6324c68240dc3",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

export const firestore = getFirestore(app);

export default app;
