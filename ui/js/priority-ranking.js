document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('priority-rows');
    if (!tbody) return;

    // Initialize with empty state
    updateTable([]);

    // Setup real-time listener
    listenToPotholes((potholes) => {
        updateTable(potholes);
    });
});

function updateTable(potholes) {
    const tbody = document.getElementById('priority-rows');
    if (!tbody) return;

    if (potholes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-data">No damage reports to rank</td></tr>';
        return;
    }

    // Add priority scores and sort
    const ranked = potholes
        .map(p => ({ 
            ...p, 
            priority: calculatePriority(p),
            traffic: 'High', // Placeholder - replace with real data later
            recurrence: p.frequency || 1,
            status: 'Pending' // Placeholder
        }))
        .sort((a, b) => b.priority - a.priority)
        .slice(0, 10); // Top 10

    tbody.innerHTML = ranked.map((p, i) => `
        <tr>
            <td>${i + 1}</td>
            <td>${p.location || 'Unnamed Road'}</td>
            <td>${p.lat.toFixed(4)}, ${p.lng.toFixed(4)}</td>
            <td><span class="severity ${p.severity}">${p.severity}</span></td>
            <td>${p.traffic}</td>
            <td>${p.recurrence}</td>
            <td>${p.priority}/5</td>
            <td><span class="status pending">${p.status}</span></td>
        </tr>
    `).join('');
}