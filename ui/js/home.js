document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('road-map')) return;

    let map;
    let markerGroup;
    let heatLayer = null;
    let currentPotholes = [];
    let currentFilter = 'all';
    let initialBoundsFit = false;

    // Define base map layers
    const streetMap = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    });

    const darkMatter = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    });

    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, USDA, USGS'
    });

    // Retrieve active layer name from localStorage
    const savedLayerName = localStorage.getItem('map_layer') || 'Street Map';
    let defaultLayer = streetMap;
    if (savedLayerName === 'Dark Mode') defaultLayer = darkMatter;
    else if (savedLayerName === 'Satellite') defaultLayer = satellite;

    // Initialize map
    map = L.map('road-map', {
        center: [30.9628, 76.8425],
        zoom: 13,
        layers: [defaultLayer]
    });

    // Add layer controls
    const baseMaps = {
        "Street Map": streetMap,
        "Dark Mode": darkMatter,
        "Satellite": satellite
    };
    L.control.layers(baseMaps, null, { collapsed: false, position: 'bottomleft' }).addTo(map);

    // Save layer choice when changed
    map.on('baselayerchange', (e) => {
        localStorage.setItem('map_layer', e.name);
    });

    markerGroup = L.featureGroup().addTo(map);

    // Load roads GeoJSON
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

    const markerColors = { severe:'#C0392B', moderate:'#E67E22', minor:'#F1C40F' };

    // Function to render markers or heatmap
    function renderMap() {
        markerGroup.clearLayers();
        if (heatLayer) {
            map.removeLayer(heatLayer);
            heatLayer = null;
        }

        const filtered = currentFilter === 'all'
            ? currentPotholes
            : currentPotholes.filter(p => p.severity === currentFilter);

        const isHeatmap = document.getElementById('heatmap-toggle')?.checked;

        if (isHeatmap) {
            const points = filtered.map(p => [
                p.lat, 
                p.lng, 
                p.severity === 'severe' ? 1.0 : p.severity === 'moderate' ? 0.6 : 0.3
            ]);
            heatLayer = L.heatLayer(points, { radius: 25, blur: 15, maxZoom: 17 }).addTo(map);
        } else {
            filtered.forEach(p => {
                const isFixed = p.status && p.status.toLowerCase() === 'fixed';
                const fillColor = isFixed ? '#27ae60' : (markerColors[p.severity] || '#999');
                
                L.circleMarker([p.lat, p.lng], {
                    radius: 10,
                    fillColor: fillColor,
                    color: '#fff',
                    weight: 1.5,
                    fillOpacity: 0.85
                }).addTo(markerGroup).bindPopup(`
                    <strong style="font-family: inherit; font-size: 14px;">${p.location || 'Unknown Location'}</strong><br>
                    <span style="font-size: 12px; color: #555;">Severity: <b style="text-transform: capitalize;">${p.severity}</b></span><br>
                    <span style="font-size: 12px; color: #555;">Status: <b style="text-transform: capitalize; color: ${isFixed ? '#27ae60' : '#e67e22'};">${p.status || 'Pending'}</b></span><br>
                    <span style="font-size: 11px; color: #777;">Coords: ${p.lat.toFixed(5)}, ${p.lng.toFixed(5)}</span>
                `);
            });
        }

        // Auto-fit bounds once on initial data receipt
        if (!initialBoundsFit && currentPotholes.length > 0) {
            const allBounds = L.featureGroup(
                currentPotholes.map(p => L.circleMarker([p.lat, p.lng]))
            ).getBounds();
            if (allBounds.isValid()) {
                map.fitBounds(allBounds, { maxZoom: 15, padding: [40, 40] });
                initialBoundsFit = true;
            }
        }
    }

    // Function to update statistics/KPIs
    function updateStatistics() {
        // Update top KPI cards
        const totalDamageEl = document.getElementById('total-damage');
        const highPriorityEl = document.getElementById('high-priority');

        if (totalDamageEl) totalDamageEl.textContent = currentPotholes.length;
        
        const severeCount = currentPotholes.filter(p => p.severity === 'severe').length;
        if (highPriorityEl) highPriorityEl.textContent = severeCount;

        // Update filter button badges
        const moderateCount = currentPotholes.filter(p => p.severity === 'moderate').length;
        const minorCount = currentPotholes.filter(p => p.severity === 'minor').length;

        const badgeAll = document.getElementById('badge-all');
        const badgeSevere = document.getElementById('badge-severe');
        const badgeModerate = document.getElementById('badge-moderate');
        const badgeMinor = document.getElementById('badge-minor');

        if (badgeAll) badgeAll.textContent = currentPotholes.length;
        if (badgeSevere) badgeSevere.textContent = severeCount;
        if (badgeModerate) badgeModerate.textContent = moderateCount;
        if (badgeMinor) badgeMinor.textContent = minorCount;
    }

    // Filter Buttons Event Handlers
    const filterGroup = document.getElementById('map-filters');
    if (filterGroup) {
        filterGroup.querySelectorAll('.map-tool-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                filterGroup.querySelectorAll('.map-tool-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                renderMap();
            });
        });
    }

    // Heatmap Toggle Event Handler
    document.getElementById('heatmap-toggle')?.addEventListener('change', () => {
        renderMap();
    });

    // Recenter Button Event Handler
    document.getElementById('live-recenter')?.addEventListener('click', async () => {
        try {
            const resp = await fetch('/api/gps');
            if (resp.ok) {
                const data = await resp.json();
                if (data.lat && data.lng) {
                    map.setView([data.lat, data.lng], 16);
                    L.popup()
                        .setLatLng([data.lat, data.lng])
                        .setContent(`<strong>🎯 Active Device</strong><br>${data.location || 'Current Position'}`)
                        .openOn(map);
                    return;
                }
            }
        } catch (e) {
            console.warn("Could not query active device GPS: ", e);
        }

        // Fallback: Recenter on the latest pothole coordinate
        if (currentPotholes.length > 0) {
            const sorted = [...currentPotholes].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            const latest = sorted[0];
            map.setView([latest.lat, latest.lng], 15);
            L.popup()
                .setLatLng([latest.lat, latest.lng])
                .setContent(`<strong>Latest Incident: ${latest.location || 'Pothole'}</strong>`)
                .openOn(map);
        } else {
            map.setView([30.9628, 76.8425], 13);
        }
    });

    L.control.scale({imperial:false}).addTo(map);

    // Setup real-time listener
    listenToPotholes((potholes) => {
        currentPotholes = potholes;
        updateStatistics();
        renderMap();
    });
});