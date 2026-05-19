let allPotholes = [];

document.addEventListener('DOMContentLoaded', () => {
    const reportsList = document.getElementById('reports-list');
    const reportCount = document.getElementById('report-count');
    const updateTime = document.getElementById('update-time');
    
    if (!reportsList || !reportCount) return;

    // Initialize with current data
    updateUI(allPotholes);

    // Setup real-time listener (Firebase)
    listenToPotholes((potholes) => {
        allPotholes = potholes;
        updateUI(potholes);
    });

    // Setup filters
    setupFilters();
    
    // Refresh button
    document.getElementById('refresh-btn')?.addEventListener('click', () => {
        document.getElementById('update-time').textContent = 
            new Date().toLocaleString('en-IN', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
    });

    // Clear All button
    document.getElementById('clear-btn')?.addEventListener('click', async () => {
        if (confirm("Are you sure you want to delete ALL recent reports? This will remove them from the database permanently.")) {
            try {
                if (typeof firebase !== 'undefined') {
                    await firebase.database().ref('potholes').remove();
                    console.log("All reports cleared!");
                }
            } catch (e) {
                console.error("Error clearing reports: ", e);
                alert("Failed to clear reports.");
            }
        }
    });
});

function updateUI(potholes) {
    const reportCount = document.getElementById('report-count');
    const updateTime = document.getElementById('update-time');
    const reportsList = document.getElementById('reports-list');
    
    if (!reportCount || !updateTime || !reportsList) return;

    reportCount.textContent = potholes.length;
    updateTime.textContent = new Date().toLocaleString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    renderReports(potholes);
}

function renderReports(potholes) {
    const container = document.getElementById('reports-list');
    
    if (potholes.length === 0) {
        container.innerHTML = '<div class="no-reports">No damage reports match current filters</div>';
        return;
    }

    const sorted = potholes.sort((a, b) => 
        new Date(b.timestamp) - new Date(a.timestamp)
    );

    container.innerHTML = sorted.map(p => `
        <div class="report-item" data-severity="${p.severity}" id="report-${p.id}">
            <div class="report-header">
                <div>
                    <span class="severity-badge ${p.severity}">${p.severity}</span>
                    <span class="report-timestamp">${new Date(p.timestamp).toLocaleTimeString()}</span>
                </div>
                <button class="delete-single-btn" onclick="deleteReport('${p.id}')" title="Delete Report">🗑️</button>
            </div>
            ${p.image_url ? `<img src="${p.image_url}" class="report-image clickable-image" alt="Pothole Snapshot" onclick="openImageModal('${p.image_url}')">` : ''}
            <div class="report-location">${p.location || 'Unnamed Location'}</div>
            <div class="report-coords">📍 ${p.lat.toFixed(4)}, ${p.lng.toFixed(4)}</div>
            ${p.confidence ? `<div class="report-confidence">Confidence: ${Math.round(p.confidence * 100)}%</div>` : ''}
        </div>
    `).join('');
}

function setupFilters() {
    document.querySelectorAll('.filter-btn').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(btn => 
                btn.classList.remove('active')
            );
            button.classList.add('active');

            const filter = button.dataset.filter;
            const filtered = filter === 'all' 
                ? allPotholes 
                : allPotholes.filter(p => p.severity === filter);
            
            document.getElementById('report-count').textContent = filtered.length;
            renderReports(filtered);
        });
    });
}

// Delete single report
window.deleteReport = async function(id) {
    if (confirm("Are you sure you want to delete this specific report?")) {
        try {
            if (typeof firebase !== 'undefined') {
                await firebase.database().ref('potholes').child(id).remove();
            }
        } catch (e) {
            console.error("Error deleting report: ", e);
            alert("Failed to delete report.");
        }
    }
}

// ─── GPS Poller — Gets real GPS from server (ADB via USB) ────────────

let currentGPS = { lat: null, lng: null, accuracy: null };
let currentLocationName = null;
let gpsInterval = null;

function startGPSPolling() {
    console.log("GPS polling from: /api/gps (ADB USB)");

    // Poll GPS every 3 seconds from Flask server
    gpsInterval = setInterval(async () => {
        try {
            const resp = await fetch('/api/gps');
            if (resp.ok) {
                const data = await resp.json();
                if (data.lat && data.lng) {
                    currentGPS.lat = data.lat;
                    currentGPS.lng = data.lng;
                    currentGPS.accuracy = data.accuracy;
                    currentLocationName = data.location;
                    
                    const gpsBadge = document.getElementById('gps-status');
                    if (gpsBadge) {
                        gpsBadge.textContent = 'GPS: Locked';
                        gpsBadge.className = 'status-badge online';
                    }
                }
            }
        } catch (e) {
            // Silent — server might be busy
        }
    }, 3000);

    // Get initial GPS immediately
    fetch('/api/gps')
        .then(r => r.json())
        .then(data => {
            if (data.lat && data.lng) {
                currentGPS.lat = data.lat;
                currentGPS.lng = data.lng;
                currentLocationName = data.location;
                console.log("GPS locked:", currentLocationName);
                
                const gpsBadge = document.getElementById('gps-status');
                if (gpsBadge) {
                    gpsBadge.textContent = 'GPS: Locked';
                    gpsBadge.className = 'status-badge online';
                }
            }
        })
        .catch(() => {});
}

function stopGPSPolling() {
    if (gpsInterval) {
        clearInterval(gpsInterval);
        gpsInterval = null;
    }
    currentGPS = { lat: null, lng: null, accuracy: null };
    currentLocationName = null;
    
    const gpsBadge = document.getElementById('gps-status');
    if (gpsBadge) {
        gpsBadge.textContent = 'GPS: Acquiring...';
        gpsBadge.className = 'status-badge offline';
    }
}


// ─── Video Integration Logic ─────────────────────────────────────────

let streamInterval;
let isDetecting = false;
let lastFirebasePush = 0;

document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-stream-btn');
    const stopBtn = document.getElementById('stop-stream-btn');
    const ipWebcamInput = document.getElementById('ip-webcam-url');
    const modelApiInput = document.getElementById('model-api-url');
    const videoPlaceholder = document.getElementById('video-placeholder');
    const cameraStream = document.getElementById('camera-stream');
    const detectionOverlay = document.getElementById('detection-overlay');
    const statusBadge = document.getElementById('inference-status');

    if (!startBtn) return;

    // Set default model URL to local Flask server
    if (!localStorage.getItem('savedModelUrl')) {
        modelApiInput.value = 'http://localhost:5000/api/predict';
    }

    // Load saved URLs
    if (localStorage.getItem('savedWebcamUrl')) {
        ipWebcamInput.value = localStorage.getItem('savedWebcamUrl');
    }
    if (localStorage.getItem('savedModelUrl')) {
        modelApiInput.value = localStorage.getItem('savedModelUrl');
    }

    startBtn.addEventListener('click', () => {
        const webcamUrl = ipWebcamInput.value.trim();
        const modelUrl = modelApiInput.value.trim();

        if (!webcamUrl || !modelUrl) {
            alert("Please enter both URLs.");
            return;
        }

        localStorage.setItem('savedWebcamUrl', webcamUrl);
        localStorage.setItem('savedModelUrl', modelUrl);

        // Start GPS polling from server (ADB USB)
        startGPSPolling();

        // Setup UI
        startBtn.disabled = true;
        stopBtn.disabled = false;
        videoPlaceholder.style.display = 'none';
        cameraStream.style.display = 'block';
        detectionOverlay.style.display = 'block';
        statusBadge.textContent = 'Connecting...';
        statusBadge.className = 'status-badge';

        // Connect to IP Webcam video stream
        let videoUrl = webcamUrl;
        if (!videoUrl.endsWith('/video') && !videoUrl.endsWith('/shot.jpg')) {
            videoUrl = videoUrl.replace(/\/$/, '') + '/video';
        }
        cameraStream.src = videoUrl;

        cameraStream.onload = () => {
            statusBadge.textContent = 'Online & Detecting';
            statusBadge.className = 'status-badge online';
            detectionOverlay.width = cameraStream.clientWidth;
            detectionOverlay.height = cameraStream.clientHeight;
            
            if (!isDetecting) {
                isDetecting = true;
                startInferenceLoop(modelUrl);
            }
        };

        cameraStream.onerror = (e) => {
            console.warn("Camera stream error:", e);
            statusBadge.textContent = 'Stream Warning';
            statusBadge.className = 'status-badge offline';
        };
        
        // Force start after 2 seconds if onload doesn't fire (MJPEG quirk)
        setTimeout(() => {
            if (!isDetecting && cameraStream.src) {
                statusBadge.textContent = 'Online (Forced)';
                statusBadge.className = 'status-badge online';
                isDetecting = true;
                startInferenceLoop(modelUrl);
            }
        }, 2000);
    });

    stopBtn.addEventListener('click', stopDetection);

    function stopDetection() {
        isDetecting = false;
        clearInterval(streamInterval);
        stopGPSPolling();
        startBtn.disabled = false;
        stopBtn.disabled = true;
        cameraStream.src = "";
        cameraStream.style.display = 'none';
        detectionOverlay.style.display = 'none';
        videoPlaceholder.style.display = 'flex';
        statusBadge.textContent = 'Offline';
        statusBadge.className = 'status-badge offline';
        
        const ctx = detectionOverlay.getContext('2d');
        ctx.clearRect(0, 0, detectionOverlay.width, detectionOverlay.height);
    }

    function startInferenceLoop(modelUrl) {
        // Use a flag to prevent overlapping inference calls
        let inferenceInProgress = false;

        streamInterval = setInterval(async () => {
            if (!isDetecting || !cameraStream.complete || cameraStream.naturalWidth === 0) return;
            if (inferenceInProgress) return; // Skip if previous frame still processing

            inferenceInProgress = true;

            try {
                const tempCanvas = document.createElement('canvas');
                // Scale down for faster inference (max 640px wide)
                const scale = Math.min(1, 640 / cameraStream.naturalWidth);
                tempCanvas.width = cameraStream.naturalWidth * scale;
                tempCanvas.height = cameraStream.naturalHeight * scale;
                const ctx = tempCanvas.getContext('2d');
                ctx.drawImage(cameraStream, 0, 0, tempCanvas.width, tempCanvas.height);

                // Get JPEG blob for inference
                const blob = await new Promise(resolve => tempCanvas.toBlob(resolve, 'image/jpeg', 0.6));
                if (!blob) { inferenceInProgress = false; return; }

                const formData = new FormData();
                formData.append('image', blob, 'frame.jpg');

                // Tell server to save image when ready to push to Firebase
                const now = Date.now();
                const readyToSave = (now - lastFirebasePush >= 2000);
                const fetchUrl = readyToSave ? modelUrl + '?save_image=1' : modelUrl;

                const response = await fetch(fetchUrl, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    // Server returns {predictions: [...], image_url: "..."}
                    const predictions = data.predictions || data;
                    const imageUrl = data.image_url || null;

                    // Draw bounding boxes (isolated — errors here must NOT block saving)
                    try {
                        drawPredictions(predictions, scale);
                    } catch (drawErr) {
                        console.warn("Draw error:", drawErr);
                    }

                    // Save to Firebase (critical path)
                    handleDetections(predictions, imageUrl, blob);
                }
            } catch (error) {
                console.error("Inference Error:", error);
            } finally {
                inferenceInProgress = false;
            }
        }, 800);
    }

    function drawPredictions(predictions, inferenceScale = 1) {
        if (!Array.isArray(predictions)) return;
        const ctx = detectionOverlay.getContext('2d');
        detectionOverlay.width = cameraStream.clientWidth;
        detectionOverlay.height = cameraStream.clientHeight;
        ctx.clearRect(0, 0, detectionOverlay.width, detectionOverlay.height);

        // Scale from inference resolution to display resolution
        const scaleX = detectionOverlay.width / (cameraStream.naturalWidth * inferenceScale);
        const scaleY = detectionOverlay.height / (cameraStream.naturalHeight * inferenceScale);

        predictions.forEach(pred => {
            const x = pred.xmin * scaleX;
            const y = pred.ymin * scaleY;
            const width = (pred.xmax - pred.xmin) * scaleX;
            const height = (pred.ymax - pred.ymin) * scaleY;

            let color = '#f1c40f';
            if (pred.severity === 'severe') color = '#e74c3c';
            else if (pred.severity === 'moderate') color = '#e67e22';

            ctx.strokeStyle = color;
            ctx.lineWidth = 3;
            ctx.strokeRect(x, y, width, height);

            ctx.fillStyle = color;
            const label = `${pred.class || 'Pothole'} (${Math.round((pred.confidence || 0) * 100)}%)`;
            ctx.font = '14px Arial';
            const textWidth = ctx.measureText(label).width;
            ctx.fillRect(x, y > 20 ? y - 20 : y, textWidth + 10, 20);

            ctx.fillStyle = '#fff';
            ctx.fillText(label, x + 5, y > 20 ? y - 5 : y + 15);
        });
    }

    async function handleDetections(predictions, serverImageUrl, imageBlob) {
        if (!Array.isArray(predictions) || predictions.length === 0) return;

        // Push to Firebase max once every 2 seconds
        const now = Date.now();
        if (now - lastFirebasePush < 2000) return;

        // Find worst severity
        let worstSeverity = null;
        let bestConf = 0;

        predictions.forEach(pred => {
            if (pred.confidence > bestConf) bestConf = pred.confidence;
            if (!worstSeverity) {
                worstSeverity = pred.severity || 'minor';
            } else if (pred.severity === 'severe') {
                worstSeverity = 'severe';
            } else if (pred.severity === 'moderate' && worstSeverity !== 'severe') {
                worstSeverity = 'moderate';
            }
        });

        if (worstSeverity && typeof firebase !== 'undefined') {
            // Do not save until GPS is locked
            if (!currentGPS.lat || currentGPS.lat === 0) {
                console.warn("Detection skipped: Waiting for GPS lock...");
                return;
            }

            lastFirebasePush = now;
            
            const lat = currentGPS.lat;
            const lng = currentGPS.lng;
            const location = currentLocationName || `${lat.toFixed(4)}, ${lng.toFixed(4)}`;

            try {
                // 1. Upload to Firebase Storage
                let cloudImageUrl = null;
                if (imageBlob) {
                    try {
                        const timestamp = Date.now();
                        const storageRef = firebase.storage().ref();
                        const imageRef = storageRef.child(`pothole_images/img_${timestamp}.jpg`);
                        
                        console.log("Uploading image to Firebase Storage...");
                        const uploadTask = imageRef.put(imageBlob);
                        const timeoutPromise = new Promise((_, reject) => 
                            setTimeout(() => reject(new Error("Storage upload timeout")), 5000)
                        );
                        
                        const snapshot = await Promise.race([uploadTask, timeoutPromise]);
                        cloudImageUrl = await snapshot.ref.getDownloadURL();
                        console.log("Image uploaded successfully:", cloudImageUrl);
                    } catch (storageErr) {
                        console.error("Firebase Storage upload failed:", storageErr);
                        // Fallback to local server image if cloud upload fails
                        if (serverImageUrl) {
                            cloudImageUrl = window.location.origin + serverImageUrl;
                        }
                    }
                } else if (serverImageUrl) {
                    cloudImageUrl = window.location.origin + serverImageUrl;
                }

                // 2. Save to Firebase Realtime Database
                const db = firebase.database();
                const newRef = db.ref('potholes').push();
                
                const payload = {
                    lat: lat,
                    lng: lng,
                    severity: worstSeverity,
                    confidence: Math.round(bestConf * 100) / 100,
                    location: location,
                    timestamp: firebase.database.ServerValue.TIMESTAMP,
                    source: "live_detection"
                };

                if (cloudImageUrl) {
                    payload.image_url = cloudImageUrl;
                }
                
                await newRef.set(payload);
                console.log(`✅ Detection saved: ${location} | ${worstSeverity} | ${bestConf.toFixed(2)}` +
                    (cloudImageUrl ? ` 📷` : ''));
            } catch (err) {
                console.error("Firebase Database save error:", err);
            }
        }
    }
});

// ─── Image Modal Logic ────────────────────────────────────────────────

function openImageModal(imgUrl) {
    const modal = document.getElementById('image-modal');
    const modalImg = document.getElementById('modal-image');
    const downloadBtn = document.getElementById('modal-download');
    
    if (modal && modalImg && downloadBtn) {
        modal.style.display = "block";
        modalImg.src = imgUrl;
        downloadBtn.href = imgUrl;
        
        // Extract filename for download attribute
        const filename = imgUrl.substring(imgUrl.lastIndexOf('/') + 1) || 'pothole_detection.jpg';
        downloadBtn.download = filename;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Modal close logic
    const modal = document.getElementById('image-modal');
    const closeBtn = document.getElementById('modal-close');
    
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = "none";
        }
    }
    
    // Close on background click
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
});