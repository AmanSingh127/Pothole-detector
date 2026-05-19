// js/config.js

// --- Firebase Config (replace with your own) ---
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "your-project.firebaseapp.com",
  databaseURL: "https://your-project-default-rtdb.firebaseio.com",
  projectId: "your-project",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef123456"
};

// --- Baddi Road Segments (GeoJSON Polygons) ---
// Use https://geojson.io to draw these, then paste here
const BADDI_ROADS = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: { road_name: "MHS Road" },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [76.8400, 30.9600],
            [76.8450, 30.9600],
            [76.8450, 30.9650],
            [76.8400, 30.9650],
            [76.8400, 30.9600]
          ]
        ]
      }
    },
    // Add more roads here later
    {
      type: "Feature",
      properties: { road_name: "Barotiwala Industrial Link" },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [76.8500, 30.9700],
            [76.8550, 30.9700],
            [76.8550, 30.9750],
            [76.8500, 30.9750],
            [76.8500, 30.9700]
          ]
        ]
      }
    }
  ]
};