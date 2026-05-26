document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('priority-rows');
    if (!tbody) return;

    // Initialize with empty state
    updateTable([]);

    // Setup real-time listener
    listenToPotholes((potholes) => {
        updateTable(potholes);
    });

    // Clear Fixed button
    const clearFixedBtn = document.getElementById('clear-fixed-btn');
    if (clearFixedBtn) {
        clearFixedBtn.addEventListener('click', async () => {
            if (confirm("Are you sure you want to clear all Fixed/resolved pothole reports from the database?")) {
                try {
                    if (typeof firebase !== 'undefined') {
                        const db = firebase.database();
                        const snapshot = await db.ref('potholes').once('value');
                        const promises = [];
                        snapshot.forEach(child => {
                            const val = child.val();
                            if (val && val.status && val.status.toLowerCase() === 'fixed') {
                                promises.push(db.ref('potholes').child(child.key).remove());
                            }
                        });
                        if (promises.length > 0) {
                            await Promise.all(promises);
                            console.log(`Cleared ${promises.length} fixed reports!`);
                        } else {
                            alert("No reports with 'Fixed' status found to clear.");
                        }
                    }
                } catch (e) {
                    console.error("Error clearing fixed reports: ", e);
                    alert("Failed to clear fixed reports.");
                }
            }
        });
    }
});

window.changeStatus = async function(selectEl, id) {
    const newStatus = selectEl.value;
    selectEl.className = `status ${newStatus.toLowerCase().replace(' ', '-')}`;
    await window.updatePotholeStatus(id, newStatus);
};

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
            status: p.status || 'Pending'
        }))
        .sort((a, b) => b.priority - a.priority);

    tbody.innerHTML = ranked.map((p, i) => {
        const statusVal = p.status || 'Pending';
        const statusClass = statusVal.toLowerCase().replace(' ', '-');
        
        const selectHtml = `
            <select class="status ${statusClass}" onchange="changeStatus(this, '${p.id}')" style="border: 1px solid rgba(0,0,0,0.05); font-family: inherit; font-size: inherit; font-weight: inherit; padding: 0.2rem 0.4rem; border-radius: 4px; cursor: pointer; outline: none;">
                <option value="Pending" ${statusClass === 'pending' ? 'selected' : ''}>Pending</option>
                <option value="Scheduled" ${statusClass === 'scheduled' ? 'selected' : ''}>Scheduled</option>
                <option value="In Progress" ${statusClass === 'in-progress' ? 'selected' : ''}>In Progress</option>
                <option value="Fixed" ${statusClass === 'fixed' ? 'selected' : ''}>Fixed</option>
            </select>
        `;

        return `
            <tr>
                <td>${i + 1}</td>
                <td>${p.location || 'Unnamed Road'}</td>
                <td>${p.lat.toFixed(4)}, ${p.lng.toFixed(4)}</td>
                <td><span class="severity ${p.severity}">${p.severity}</span></td>
                <td>${p.traffic}</td>
                <td>${p.recurrence}</td>
                <td><span class="score">${p.priority}/5</span></td>
                <td>${selectHtml}</td>
            </tr>
        `;
    }).join('');
}