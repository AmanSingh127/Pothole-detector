// js/firebase-init.js
const firebaseConfig = {
  apiKey: "AIzaSyDtjNhBzZpm3liU9b-JW4DTOg66k5G12xk",
  authDomain: "roadsentinel-87fc3.firebaseapp.com",
  databaseURL: "https://roadsentinel-87fc3-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "roadsentinel-87fc3",
  storageBucket: "roadsentinel-87fc3.firebasestorage.app",
  messagingSenderId: "758669021674",
  appId: "1:758669021674:web:8ad6282667819cd9406293"
};

// Initialize only once
if (!firebase.apps.length) {
  firebase.initializeApp(firebaseConfig);
}

// Export database instance
const db = firebase.database();