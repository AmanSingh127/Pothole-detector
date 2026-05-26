// js/data-loader.js
let globalGroupedMap = new Map();

function haversineDistance(lat1, lng1, lat2, lng2) {
    const R = 6371000; // Earth's radius in meters
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

function groupPotholes(potholes) {
    const zones = [];
    const distanceThreshold = 20; // 20 meters

    potholes.forEach(p => {
        const lat = parseFloat(p.lat);
        const lng = parseFloat(p.lng);
        if (isNaN(lat) || isNaN(lng)) return;

        const status = (p.status || 'Pending').trim();

        let matchedZone = null;
        for (const zone of zones) {
            if (zone.status.toLowerCase() === status.toLowerCase()) {
                const dist = haversineDistance(lat, lng, zone.lat, zone.lng);
                if (dist <= distanceThreshold) {
                    matchedZone = zone;
                    break;
                }
            }
        }

        if (matchedZone) {
            matchedZone.frequency += (p.frequency || 1);
            matchedZone.childIds.push(p.id);
            if (p.confidence && p.confidence > matchedZone.confidence) {
                matchedZone.confidence = p.confidence;
            }
            if (p.timestamp && (!matchedZone.timestamp || new Date(p.timestamp) > new Date(matchedZone.timestamp))) {
                matchedZone.timestamp = p.timestamp;
                matchedZone.location = p.location || matchedZone.location;
                if (p.image_url) {
                    matchedZone.image_url = p.image_url;
                }
            }
            const severityRank = { severe: 3, moderate: 2, minor: 1 };
            if (p.severity && (severityRank[p.severity] > severityRank[matchedZone.severity])) {
                matchedZone.severity = p.severity;
            }
        } else {
            zones.push({
                id: p.id,
                lat: lat,
                lng: lng,
                location: p.location || 'Unnamed Location',
                severity: p.severity || 'minor',
                confidence: p.confidence || 0,
                timestamp: p.timestamp,
                image_url: p.image_url || '',
                status: status,
                frequency: p.frequency || 1,
                childIds: [p.id]
            });
        }
    });

    globalGroupedMap.clear();
    zones.forEach(zone => {
        globalGroupedMap.set(zone.id, zone.childIds);
    });

    return zones;
}

window.deleteReport = async function(id) {
    const idsToDelete = globalGroupedMap.has(id) ? globalGroupedMap.get(id) : [id];
    if (confirm(`Are you sure you want to delete this report?`)) {
        try {
            if (typeof firebase !== 'undefined') {
                const db = firebase.database();
                const promises = idsToDelete.map(childId => db.ref('potholes').child(childId).remove());
                await Promise.all(promises);
                console.log("Reports deleted successfully!");
            }
        } catch (e) {
            console.error("Error deleting reports: ", e);
            alert("Failed to delete report.");
        }
    }
};

window.updatePotholeStatus = async function(id, newStatus) {
    const idsToUpdate = globalGroupedMap.has(id) ? globalGroupedMap.get(id) : [id];
    try {
        if (typeof firebase !== 'undefined') {
            const db = firebase.database();
            const promises = idsToUpdate.map(childId => 
                db.ref('potholes').child(childId).update({ status: newStatus })
            );
            await Promise.all(promises);
            console.log(`Status updated to ${newStatus} for reports:`, idsToUpdate);
        }
    } catch (e) {
        console.error("Error updating status: ", e);
        alert("Failed to update status.");
    }
};

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
          // Normalize image path/url naming discrepancies and slashes
          if (data.image_path && !data.image_url) {
            let path = data.image_path.replace(/\\/g, '/');
            if (path.startsWith('detections/')) {
              path = '/' + path;
            }
            data.image_url = path;
          }
          rawPotholes.push(data);
        });

        resolve(groupPotholes(rawPotholes));
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
      // Normalize image path/url naming discrepancies and slashes
      if (data.image_path && !data.image_url) {
        let path = data.image_path.replace(/\\/g, '/');
        if (path.startsWith('detections/')) {
          path = '/' + path;
        }
        data.image_url = path;
      }
      potholes.push(data);
    });
    
    callback(groupPotholes(potholes));
  });
}