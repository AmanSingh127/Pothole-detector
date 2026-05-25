"""
RoadSentinel Web Server
=======================
Flask server that:
  1. Serves the RoadSentinel web UI
  2. Provides /api/predict endpoint for live YOLO inference
  3. Provides /api/gps endpoint for real-time GPS via ADB (USB)
  4. Serves detection images from the detections/ folder

Usage:
    python server.py
    Then open http://localhost:5000 in your browser
"""

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import cv2
import numpy as np
import re
import base64
import math
import subprocess
import threading
import time
from ultralytics import YOLO
import sqlite3
import requests
from geopy.geocoders import Nominatim

from functools import wraps

app = Flask(__name__, static_folder='ui', static_url_path='')
CORS(app)

# Firebase config (same as dashcam_tracker)
FIREBASE_DB_URL = "https://roadsentinel-87fc3-default-rtdb.asia-southeast1.firebasedatabase.app"

# API Key Configuration (Simulating commercial LLM / Map API protection)
ROADSENTINEL_API_KEY = "rs_api_key_8d9f10a7b4c2d3e4f5"

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("x-api-key")
        if not api_key or api_key != ROADSENTINEL_API_KEY:
            return jsonify({"error": "Unauthorized. Missing or invalid API key."}), 401
        return f(*args, **kwargs)
    return decorated

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "runs", "detect", "train", "weights", "best.pt")
DB_PATH = os.path.join(BASE_DIR, "potholes.db")
DETECTIONS_DIR = os.path.join(BASE_DIR, "detections")

# Load YOLO model once at startup
print("Loading YOLO model...")
if not os.path.exists(MODEL_PATH):
    for alt in ["best.pt", "yolov8n.pt"]:
        p = os.path.join(BASE_DIR, alt)
        if os.path.exists(p):
            MODEL_PATH = p
            break
model = YOLO(MODEL_PATH)
print(f"Model loaded: {MODEL_PATH}")


def conf_to_severity(conf):
    if conf >= 0.8:
        return "severe"
    elif conf >= 0.6:
        return "moderate"
    return "minor"


# ─── ADB GPS Poller (gets GPS from phone via USB) ────────────────────

class ADBGPSPoller:
    """Polls GPS coordinates from phone via ADB over USB."""

    def __init__(self, poll_interval=2.0):
        self.lat = None
        self.lon = None
        self.accuracy = None
        self.timestamp = 0
        self.lock = threading.Lock()
        self.running = True
        self.poll_interval = poll_interval
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print("  ADB GPS poller started (USB)")

    def _poll_loop(self):
        while self.running:
            try:
                result = subprocess.run(
                    ['adb', 'shell', 'dumpsys', 'location'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    self._parse_location(result.stdout)
            except Exception:
                pass
            time.sleep(self.poll_interval)

    def _parse_location(self, output):
        best_lat, best_lon, best_acc = None, None, 9999
        pattern = r'last location=Location\[(\w+)\s+([-\d.]+),([-\d.]+)\s+hAcc=([\d.]+)'
        matches = re.findall(pattern, output)
        priority = {'gps': 0, 'fused': 1, 'network': 2}
        best_priority = 99
        for provider, lat, lon, acc in matches:
            p = priority.get(provider, 3)
            acc_f = float(acc)
            if p < best_priority or (p == best_priority and acc_f < best_acc):
                best_lat = float(lat)
                best_lon = float(lon)
                best_acc = acc_f
                best_priority = p
        if best_lat is not None:
            with self.lock:
                self.lat = best_lat
                self.lon = best_lon
                self.accuracy = best_acc
                self.timestamp = time.time()

    def get(self):
        with self.lock:
            if self.lat is not None and (time.time() - self.timestamp) < 120:
                return self.lat, self.lon, self.accuracy
        return None, None, None

    def stop(self):
        self.running = False


# ─── Reverse Geocoder with caching ───────────────────────────────────

geolocator = Nominatim(user_agent="roadsentinel_server_v2")
geo_cache = {"lat": None, "lon": None, "name": None}

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def reverse_geocode(lat, lon):
    if geo_cache["lat"] is not None:
        dist = _haversine(lat, lon, geo_cache["lat"], geo_cache["lon"])
        if dist < 50:
            return geo_cache["name"]
    try:
        loc = geolocator.reverse((lat, lon), timeout=5, addressdetails=True, zoom=18)
        if loc and 'address' in loc.raw:
            a = loc.raw['address']
            building = a.get('amenity') or a.get('building') or a.get('shop') or a.get('house_number', '')
            road = a.get('road') or a.get('pedestrian') or a.get('footway') or ''
            area = a.get('neighbourhood') or a.get('suburb') or a.get('village') or ''
            city = a.get('city') or a.get('town') or a.get('city_district') or a.get('county') or ''
            parts = [p for p in [building, road, area, city] if p]
            name = ", ".join(parts) if parts else loc.address
            geo_cache["lat"] = lat
            geo_cache["lon"] = lon
            geo_cache["name"] = name
            return name
    except Exception as e:
        print(f"  Geocoding error: {e}")
    return f"{lat:.6f}, {lon:.6f}"


# Start ADB GPS poller at server startup
print("Starting ADB GPS poller...")
try:
    gps_poller = ADBGPSPoller(poll_interval=2.0)
except Exception as e:
    print(f"  Warning: ADB GPS not available ({e})")
    gps_poller = None


# ─── Serve UI ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('ui', 'index.html')


@app.route('/<path:filename>')
def serve_ui(filename):
    return send_from_directory('ui', filename)


# ─── Serve detection images ──────────────────────────────────────────

@app.route('/detections/<path:filename>')
def serve_detection(filename):
    return send_from_directory(DETECTIONS_DIR, filename)


# ─── API: YOLO Prediction (for live detection page) ──────────────────

@app.route('/api/predict', methods=['POST'])
@require_api_key
def predict():
    """Accept an image, run YOLO inference, return predictions.
    If potholes are detected, saves the frame to detections/ folder."""
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files['image']
    img_bytes = file.read()
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({"error": "Invalid image"}), 400

    # Run YOLO
    results = model(frame, conf=0.5, verbose=False)
    result = results[0]

    predictions = []
    for box in result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        class_name = model.names.get(cls, "pothole")

        predictions.append({
            "xmin": x1, "ymin": y1, "xmax": x2, "ymax": y2,
            "confidence": conf,
            "class": class_name,
            "severity": conf_to_severity(conf)
        })

    # If potholes detected, save the frame (throttled to once per 10 seconds)
    image_url = None
    save_requested = request.args.get('save_image') == '1'
    if len(predictions) > 0 and (save_requested or (time.time() - predict.last_image_save) >= 10):
        try:
            os.makedirs(DETECTIONS_DIR, exist_ok=True)
            timestamp = int(time.time() * 1000)
            filename = f"pothole_{timestamp}.jpg"
            filepath = os.path.join(DETECTIONS_DIR, filename)

            # Draw bounding boxes on the frame before saving
            annotated = frame.copy()
            for pred in predictions:
                x1 = int(pred["xmin"])
                y1 = int(pred["ymin"])
                x2 = int(pred["xmax"])
                y2 = int(pred["ymax"])
                color = (0, 0, 255) if pred["severity"] == "severe" else \
                        (0, 165, 255) if pred["severity"] == "moderate" else (0, 255, 255)
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                label = f'{pred["class"]} {pred["confidence"]:.0%}'
                cv2.putText(annotated, label, (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            cv2.imwrite(filepath, annotated)
            image_url = f"/detections/{filename}"
            predict.last_image_save = time.time()
            print(f"  📷 Saved: {filename}")

            # Save to SQLite database
            try:
                lat = request.form.get('lat') or request.args.get('lat')
                lng = request.form.get('lng') or request.args.get('lng')
                loc = request.form.get('location') or request.args.get('location')

                if not lat and gps_poller is not None:
                    p_lat, p_lon, _ = gps_poller.get()
                    if p_lat is not None:
                        lat = p_lat
                        lng = p_lon
                        loc = reverse_geocode(p_lat, p_lon)

                lat_val = float(lat) if lat else 30.9628
                lng_val = float(lng) if lng else 76.8425
                loc_val = loc if loc else "Baddi Corridor (Simulated GPS)"
                max_conf = max(p["confidence"] for p in predictions) if predictions else 0.5

                conn = sqlite3.connect(DB_PATH)
                conn.execute(
                    "INSERT INTO potholes (timestamp, latitude, longitude, location_text, confidence, image_path) VALUES (?, ?, ?, ?, ?, ?)",
                    (datetime.now().isoformat(), lat_val, lng_val, loc_val, max_conf, image_url)
                )
                conn.commit()
                conn.close()
                print(f"  💾 Saved to SQLite: {loc_val} | Conf: {max_conf:.2f}")
            except Exception as db_err:
                print(f"  SQLite write error: {db_err}")
        except Exception as e:
            print(f"  Image save error: {e}")

    response = {"predictions": predictions}
    if image_url:
        response["image_url"] = image_url

    return jsonify(response)

predict.last_image_save = 0  # Initialize throttle timestamp


# ─── API: Upload pothole image (saves locally, avoids CORS) ──────────

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Accept a Base64 JPEG image, save to detections/ folder, return URL."""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "No image data provided"}), 400

        # Extract base64 data (strip the data:image/jpeg;base64, prefix)
        image_data = data['image']
        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]

        # Decode base64 to bytes
        img_bytes = base64.b64decode(image_data)

        # Create detections folder if needed
        os.makedirs(DETECTIONS_DIR, exist_ok=True)

        # Save with timestamp filename
        timestamp = data.get('timestamp', int(time.time() * 1000))
        filename = f"pothole_{timestamp}.jpg"
        filepath = os.path.join(DETECTIONS_DIR, filename)

        with open(filepath, 'wb') as f:
            f.write(img_bytes)

        # Return the URL path that the browser can use
        image_url = f"/detections/{filename}"
        print(f"  📷 Saved detection image: {filename}")
        return jsonify({"image_url": image_url, "filename": filename})

    except Exception as e:
        print(f"  Image upload error: {e}")
        return jsonify({"error": str(e)}), 500


# ─── API: GPS from ADB (for live detection page) ─────────────────────

@app.route('/api/gps', methods=['GET'])
def get_gps():
    """Return current GPS coordinates from phone via ADB USB, with fallback to local GPS server."""
    lat, lon, acc = None, None, None

    # 1. Try ADB poller first
    if gps_poller is not None:
        lat, lon, acc = gps_poller.get()

    # 2. If no ADB GPS, fallback to the browser-based gps_server on port 8085
    if lat is None:
        try:
            resp = requests.get("http://127.0.0.1:8085/gps", timeout=1)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("lat") is not None:
                    lat = data["lat"]
                    lon = data["lon"]
                    acc = data.get("accuracy")
        except Exception:
            pass

    if lat is not None:
        location_name = reverse_geocode(lat, lon)
        return jsonify({
            "lat": lat,
            "lng": lon,
            "accuracy": acc,
            "location": location_name
        })
    else:
        return jsonify({"lat": None, "lng": None, "location": "GPS acquiring signal...", "accuracy": None})


# ─── API: Get potholes from SQLite ────────────────────────────────────

@app.route('/api/potholes', methods=['GET'])
@require_api_key
def get_potholes():
    """Return all potholes from the local SQLite database."""
    if not os.path.exists(DB_PATH):
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM potholes ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()

    potholes = []
    for row in rows:
        potholes.append({
            "id": row["id"],
            "timestamp": row["timestamp"],
            "lat": row["latitude"],
            "lng": row["longitude"],
            "location": row["location_text"],
            "confidence": row["confidence"],
            "severity": conf_to_severity(row["confidence"] or 0),
            "image": row["image_path"]
        })
    return jsonify(potholes)


# ─── API: Stats for KPI cards ────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Return summary statistics for the dashboard KPI cards."""
    if not os.path.exists(DB_PATH):
        return jsonify({"total": 0, "severe": 0, "moderate": 0, "minor": 0})

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT confidence FROM potholes").fetchall()
    conn.close()

    total = len(rows)
    severe = sum(1 for r in rows if (r[0] or 0) >= 0.8)
    moderate = sum(1 for r in rows if 0.6 <= (r[0] or 0) < 0.8)
    minor = total - severe - moderate

    return jsonify({
        "total": total,
        "severe": severe,
        "moderate": moderate,
        "minor": minor
    })


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  RoadSentinel Web Server")
    print("=" * 50)
    print(f"  Dashboard: http://localhost:5000")
    print(f"  Live Detection: http://localhost:5000/live-detection.html")
    print(f"  API: http://localhost:5000/api/potholes")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
