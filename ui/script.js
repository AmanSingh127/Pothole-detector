// // DOM Elements
// const sidebar = document.getElementById('sidebar');
// const overlay = document.getElementById('overlay');
// const hamburger = document.getElementById('hamburger');
// const closeBtn = document.getElementById('close-sidebar');

// // Open sidebar
// if (hamburger) {
//     hamburger.addEventListener('click', () => {
//         sidebar.classList.add('active');
//         overlay.classList.add('active');
//     });
// }

// // Close sidebar
// function closeSidebar() {
//     sidebar.classList.remove('active');
//     overlay.classList.remove('active');
// }

// if (closeBtn) {
//     closeBtn.addEventListener('click', closeSidebar);
// }

// if (overlay) {
//     overlay.addEventListener('click', closeSidebar);
// }

// // Initialize map only on home page
// if (document.getElementById('road-map')) {
//     // Baddi coordinates: [30.9628, 76.8425], zoom level 13 for city view
//     const map = L.map('road-map').setView([30.9628, 76.8425], 13);

//     L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
//         attribution: '&copy; OpenStreetMap contributors'
//     }).addTo(map);

//     // Load Baddi roads from GeoJSON
//     fetch('Allroad.geojson')
//         .then(response => response.json())
//         .then(geojsonData => {
//        L.geoJSON(geojsonData, {
//         style: function(feature) {
//             const highway = feature.properties.highway;
//             if (['motorway', 'trunk'].includes(highway)) {
//                 return { color: '#C0392B', weight: 4 };
//             } else if (['primary'].includes(highway)) {
//                 return { color: '#E67E22', weight: 3 };
//             } else if (['secondary'].includes(highway)) {
//                 return { color: '#27AE60', weight: 2.5 };
//             } else if (['tertiary'].includes(highway)) {
//                 return { color: '#2980B9', weight: 2 };
//             } else if (['residential'].includes(highway)) {
//                 return { color: '#8E44AD', weight: 1.5 };
//             } else if (['service', 'unclassified'].includes(highway)) {
//                 return { color: '#7F8C8D', weight: 1 };
//             } else {
//                 return { color: '#BDC3C7', weight: 1 };
//             }
//         },
        
//         // 👇 ADD LABELS HERE 👇
//         onEachFeature: function(feature, layer) {
//         // Show either name OR highway reference (like NH 21)
//         const label = feature.properties.name || feature.properties.ref;
//         if (label) {
//             layer.bindTooltip(label, {
//                 permanent: false,
//                 direction: 'auto',
//                 offset: [0, -5],
//                 className: 'road-label'
//             });
//         }
//     }
//     }).addTo(map);
//         })
//         .catch(error => console.error('Error loading roads:', error));

//     // Baddi-specific damage points (replace with real data later)
//     const baddiDamagePoints = [
//         { lat: 30.9628, lng: 76.8425, severity: 'severe', location: 'Near Baddi Bus Stand' },
//         { lat: 30.9712, lng: 76.8510, severity: 'moderate', location: 'Barotiwala Industrial Area' },
//         { lat: 30.9550, lng: 76.8300, severity: 'minor', location: 'Nalagarh Road' },
//         { lat: 30.9680, lng: 76.8470, severity: 'severe', location: 'Baddi-Nalagarh Highway' },
//         { lat: 30.9590, lng: 76.8380, severity: 'moderate', location: 'Solan-Baddi Link Road' }
//     ];

//     const markerColors = {
//         severe: '#C0392B',
//         moderate: '#E67E22',
//         minor: '#F1C40F'
//     };

//     baddiDamagePoints.forEach(point => {
//         const marker = L.circleMarker([point.lat, point.lng], {
//             radius: 10,
//             fillColor: markerColors[point.severity],
//             color: '#fff',
//             weight: 1.5,
//             opacity: 1,
//             fillOpacity: 0.85
//         }).addTo(map);
        
//         marker.bindPopup(`<strong>${point.location}</strong><br>Severity: ${point.severity}`);
//     });

//     L.control.scale({imperial: false}).addTo(map);
// }







// DOM Elements
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');
const hamburger = document.getElementById('hamburger');
const closeBtn = document.getElementById('close-sidebar');

// Open sidebar
if (hamburger) {
    hamburger.addEventListener('click', () => {
        sidebar.classList.add('active');
        overlay.classList.add('active');
    });
}

// Close sidebar
function closeSidebar() {
    sidebar.classList.remove('active');
    overlay.classList.remove('active');
}

if (closeBtn) {
    closeBtn.addEventListener('click', closeSidebar);
}

if (overlay) {
    overlay.addEventListener('click', closeSidebar);
}

// Initialize map only on home page
if (document.getElementById('road-map')) {
    // Baddi coordinates: [30.9628, 76.8425], zoom level 13 for city view
    const map = L.map('road-map').setView([30.9628, 76.8425], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Load Baddi roads from GeoJSON
    fetch('Allroad.geojson')
        .then(response => response.json())
        .then(geojsonData => {
            L.geoJSON(geojsonData, {
                style: function(feature) {
                    const highway = feature.properties.highway;
                    if (['motorway', 'trunk'].includes(highway)) {
                        return { color: '#C0392B', weight: 4 };
                    } else if (['primary'].includes(highway)) {
                        return { color: '#E67E22', weight: 3 };
                    } else if (['secondary'].includes(highway)) {
                        return { color: '#27AE60', weight: 2.5 };
                    } else if (['tertiary'].includes(highway)) {
                        return { color: '#2980B9', weight: 2 };
                    } else if (['residential'].includes(highway)) {
                        return { color: '#8E44AD', weight: 1.5 };
                    } else if (['service', 'unclassified'].includes(highway)) {
                        return { color: '#7F8C8D', weight: 1 };
                    } else {
                        return { color: '#BDC3C7', weight: 1 };
                    }
                },
                // Show road names OR highway references (like NH105)
                onEachFeature: function(feature, layer) {
                    const label = feature.properties.name || feature.properties.ref;
                    if (label) {
                        layer.bindTooltip(label, {
                            permanent: false,
                            direction: 'auto',
                            offset: [0, -5],
                            className: 'road-label'
                        });
                    }
                }
            }).addTo(map);
        })
        .catch(error => console.error('Error loading roads:', error));

    // Load real pothole data when available (future AI outputs)
    fetch('data/potholes.json')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('No pothole data file');
        })
        .then(potholes => {
            const markerColors = {
                severe: '#C0392B',
                moderate: '#E67E22',
                minor: '#F1C40F'
            };

                potholes.forEach(point => {
            const marker = L.circleMarker([point.lat, point.lng], {
                radius: 10,
                fillColor: markerColors[point.severity],
                color: '#fff',
                weight: 1.5,
                opacity: 1,
                fillOpacity: 0.85
            }).addTo(map);
            
            marker.bindPopup(`
                <strong>${point.location || 'Unnamed Location'}</strong><br>
                Severity: ${point.severity}<br>
                ${point.timestamp ? `Detected: ${new Date(point.timestamp).toLocaleString()}` : ''}
            `);
        });

        // Calculate and update KPIs
        updateKPIs(potholes);
    })
    .catch(error => {
        console.log('No active pothole reports:', error.message);
    });

    L.control.scale({imperial: false}).addTo(map);
}
// KPI Calculation Function
function updateKPIs(potholes) {
    // Total damage points
    document.getElementById('total-damage').textContent = potholes.length;
    
    // High-priority = severe damage points
    const highPriority = potholes.filter(p => p.severity === 'severe').length;
    document.getElementById('high-priority').textContent = highPriority;
}