// js/data-loader.js
async function loadPotholeData() {
  return new Promise((resolve) => {
    const db = firebase.database();
    db.ref('potholes').once('value')
      .then(snapshot => {
        const rawPotholes = [];
        snapshot.forEach(child => {
          const data = child.val();
          data.id = child.key;
          if (typeof data.timestamp === 'number') {
            data.timestamp = new Date(data.timestamp).toISOString();
          }
          rawPotholes.push(data);
        });

        resolve(rawPotholes);
      })
      .catch(error => {
        console.error('Firebase read error:', error);
        resolve([]);
      });
  });
}

function calculatePriority(pothole) {
  // Base score from severity (non-negotiable foundation)
  let baseScore = 0;
  if (pothole.severity === 'severe') baseScore = 4;
  else if (pothole.severity === 'moderate') baseScore = 2;
  else baseScore = 1; // minor

  // Recurrence boost (max +1 to avoid overriding severity)
  const recurrenceBoost = Math.min((pothole.frequency || 1) - 1, 1); // 0 for 1 detection, 1 for 2+ detections

  // Total score (max 5)
  return Math.min(baseScore + recurrenceBoost, 5);
}


function listenToPotholes(callback) {
  const db = firebase.database();
  return db.ref('potholes').on('value', (snapshot) => {
    const potholes = [];
    snapshot.forEach(child => {
      const data = child.val();
      data.id = child.key;
      if (typeof data.timestamp === 'number') {
        data.timestamp = new Date(data.timestamp).toISOString();
      }
      potholes.push(data);
    });
    
    callback(potholes);
  });
}