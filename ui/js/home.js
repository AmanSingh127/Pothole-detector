document.addEventListener('DOMContentLoaded', async () => {
    if (!document.getElementById('road-map')) return;

    const potholes = await loadPotholeData();

    // Update KPIs
    document.getElementById('total-damage').textContent = potholes.length;
    const highPriority = potholes.filter(p => p.severity === 'severe').length;
    document.getElementById('high-priority').textContent = highPriority;

    // Initialize map 
    const map = L.map('road-map').setView([30.9628, 76.8425], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Load roads 
    fetch('Allroad.geojson')
        .then(r => r.json())
        .then(geojsonData => {
            L.geoJSON(geojsonData, {
                style: feature => {
                    const h = feature.properties.highway;
                    if (['motorway','trunk'].includes(h)) return {color:'#C0392B',weight:4};
                    if (['primary'].includes(h)) return {color:'#E67E22',weight:3};
                    if (['secondary'].includes(h)) return {color:'#27AE60',weight:2.5};
                    if (['tertiary'].includes(h)) return {color:'#2980B9',weight:2};
                    return {color:'#BDC3C7',weight:1};
                },
                onEachFeature: (f, l) => {
                    const label = f.properties.name || f.properties.ref;
                    if (label) l.bindTooltip(label, {permanent:false, offset:[0,-5]});
                }
            }).addTo(map);
        });

    // Add pothole markers
    const markerColors = { severe:'#C0392B', moderate:'#E67E22', minor:'#F1C40F' };
    potholes.forEach(p => {
        L.circleMarker([p.lat, p.lng], {
            radius: 10,
            fillColor: markerColors[p.severity],
            color: '#fff',
            weight: 1.5,
            fillOpacity: 0.85
        }).addTo(map).bindPopup(`
            <strong>${p.location || 'Unknown'}</strong><br>
            Severity: ${p.severity}
        `);
    });

    L.control.scale({imperial:false}).addTo(map);
});