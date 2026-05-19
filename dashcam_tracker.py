"""
Real-Time Dashcam Pothole Tracker
=================================
Detects potholes via YOLO from IP Webcam camera feed.
Gets precise GPS from phone via USB (ADB) — no browser/firewall needed.
Saves detections with road-level location to SQLite database.

Usage:
    python dashcam_tracker.py --ip <phone_ip>
    python dashcam_tracker.py --ip <phone_ip> --location "Fallback Location"

Requirements:
    - Phone connected via USB with USB Debugging ON
    - IP Webcam app running on phone
    - ADB installed on PC (adb.exe in PATH)
"""

import cv2
import requests
import time
import json
import math
import re
import numpy as np
from datetime import datetime
import sqlite3
import os
import subprocess
from ultralytics import YOLO
from geopy.geocoders import Nominatim
import threading
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Firebase Realtime Database URL (for web UI sync)
FIREBASE_DB_URL = "https://roadsentinel-87fc3-default-rtdb.asia-southeast1.firebasedatabase.app"


# ═══════════════════════════════════════════════════════════════════════
#  ADB GPS Poller — Gets GPS directly from phone via USB
# ═══════════════════════════════════════════════════════════════════════

class ADBGPSPoller:
    """Polls GPS coordinates from the phone via ADB over USB.
    No browser, no firewall, no network GPS server needed."""

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

    def _poll_loop(self):
        """Continuously poll GPS from ADB."""
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
        """Parse GPS coordinates from ADB dumpsys location output.
        Tries fused > gps > network providers in order of accuracy."""
        best_lat, best_lon, best_acc = None, None, 9999

        # Match: Location[provider lat,lon hAcc=X ...]
        pattern = r'last location=Location\[(\w+)\s+([-\d.]+),([-\d.]+)\s+hAcc=([\d.]+)'
        matches = re.findall(pattern, output)

        # Priority: gps > fused > network
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
        """Returns (lat, lon, accuracy) or (None, None, None) if no GPS."""
        with self.lock:
            if self.lat is not None and (time.time() - self.timestamp) < 120:
                return self.lat, self.lon, self.accuracy
        return None, None, None

    def stop(self):
        self.running = False


# ═══════════════════════════════════════════════════════════════════════
#  Frame Grabber — Threaded IP Webcam frame reader
# ═══════════════════════════════════════════════════════════════════════

class FrameGrabber:
    """Continuously grabs frames from IP Webcam's /shot.jpg endpoint."""

    def __init__(self, snapshot_url):
        self.url = snapshot_url
        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            try:
                resp = requests.get(self.url, timeout=2)
                if resp.status_code == 200:
                    arr = np.frombuffer(resp.content, dtype=np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        with self.lock:
                            self.frame = frame
            except Exception:
                time.sleep(0.1)

    def read(self):
        with self.lock:
            if self.frame is not None:
                return True, self.frame.copy()
            return False, None

    def stop(self):
        self.running = False


# ═══════════════════════════════════════════════════════════════════════
#  Geo Utilities
# ═══════════════════════════════════════════════════════════════════════

def _haversine(lat1, lon1, lat2, lon2):
    """Distance between two GPS coordinates in meters."""
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ═══════════════════════════════════════════════════════════════════════
#  Main Tracker
# ═══════════════════════════════════════════════════════════════════════

class DashcamTracker:
    def __init__(self, phone_ip, model_path="runs/detect/train/weights/best.pt",
                 conf_threshold=0.5, cooldown_sec=3.0, manual_location=None):
        # Parse phone IP for IP Webcam
        clean_ip = phone_ip.replace("http://", "").replace("https://", "")
        if ":" in clean_ip:
            ip_part, port_part = clean_ip.rsplit(":", 1)
            self.phone_url = f"http://{ip_part}:{port_part}"
        else:
            self.phone_url = f"http://{clean_ip}:8080"

        self.snapshot_url = f"{self.phone_url}/shot.jpg"
        self.manual_location = manual_location

        # Geocoding with caching (avoids hammering Nominatim while driving)
        self.geolocator = Nominatim(user_agent="pothole_dashcam_v2")
        self._geo_cache_name = None
        self._geo_cache_lat = None
        self._geo_cache_lon = None
        self._location_lock = threading.Lock()
        self._current_display_location = manual_location

        # YOLO model
        print(f"Loading YOLO model from {model_path}...")
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.cooldown_sec = cooldown_sec
        self.last_detection_time = 0
        self.detection_count = 0

        # Database
        self.db_path = "potholes.db"
        self.detections_dir = "detections"
        os.makedirs(self.detections_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS potholes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, latitude REAL, longitude REAL,
            location_text TEXT, confidence REAL, image_path TEXT
        )''')
        # Migrate old DB if needed
        c.execute("PRAGMA table_info(potholes)")
        cols = [row[1] for row in c.fetchall()]
        if 'latitude' not in cols:
            c.execute("ALTER TABLE potholes ADD COLUMN latitude REAL")
        if 'longitude' not in cols:
            c.execute("ALTER TABLE potholes ADD COLUMN longitude REAL")
        conn.commit()
        conn.close()

    def _reverse_geocode(self, lat, lon):
        """Convert lat/lon to precise location name with building/road detail.
        Uses zoom=18 for building-level precision. Caches within 50m."""
        if self._geo_cache_lat is not None:
            dist = _haversine(lat, lon, self._geo_cache_lat, self._geo_cache_lon)
            if dist < 50:
                return self._geo_cache_name

        try:
            loc = self.geolocator.reverse(
                (lat, lon), timeout=5, addressdetails=True, zoom=18
            )
            if loc and 'address' in loc.raw:
                a = loc.raw['address']
                # Building/amenity name (e.g. "Chitkara University", "Big Bazaar")
                building = (a.get('amenity') or a.get('building') or
                            a.get('shop') or a.get('tourism') or
                            a.get('leisure') or a.get('office') or
                            a.get('house_number', ''))
                # Road name (e.g. "NH105", "MG Road")
                road = (a.get('road') or a.get('pedestrian') or
                        a.get('footway') or a.get('residential') or '')
                # Area/neighbourhood
                area = (a.get('neighbourhood') or a.get('suburb') or
                        a.get('quarter') or a.get('village') or '')
                # City/town
                city = (a.get('city') or a.get('town') or
                        a.get('city_district') or a.get('county') or '')

                parts = [p for p in [building, road, area, city] if p]
                if parts:
                    name = ", ".join(parts)
                else:
                    name = loc.address
                self._geo_cache_name = name
                self._geo_cache_lat = lat
                self._geo_cache_lon = lon
                return name
        except Exception as e:
            print(f"  Geocoding error: {e}")

        return f"Lat: {lat:.6f}, Lon: {lon:.6f}"

    def _get_location(self, gps_poller):
        """Get current location — ADB GPS first, then manual fallback."""
        lat, lon, acc = gps_poller.get()

        if lat is not None:
            name = self._reverse_geocode(lat, lon)
            with self._location_lock:
                self._current_display_location = name
            return name, lat, lon

        if self.manual_location:
            return self.manual_location, None, None

        return "No GPS signal", None, None

    def _conf_to_severity(self, conf):
        """Map confidence score to severity level for the UI."""
        if conf >= 0.8:
            return "severe"
        elif conf >= 0.6:
            return "moderate"
        return "minor"

    def _push_to_firebase(self, lat, lon, area_name, conf):
        """Push detection to Firebase Realtime Database for web UI."""
        try:
            data = {
                "lat": lat or 0,
                "lng": lon or 0,
                "severity": self._conf_to_severity(conf),
                "location": area_name,
                "confidence": round(conf, 2),
                "timestamp": {".sv": "timestamp"}
            }
            requests.post(
                f"{FIREBASE_DB_URL}/potholes.json",
                json=data, timeout=3
            )
        except Exception:
            pass  # Don't block detection if Firebase is unreachable

    def _save_detection(self, lat, lon, area_name, conf, frame):
        """Save detection to SQLite + push to Firebase."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        img_path = os.path.join(self.detections_dir, f"pothole_{ts}.jpg")
        cv2.imwrite(img_path, frame)

        # Save to local SQLite
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO potholes (timestamp,latitude,longitude,location_text,confidence,image_path) VALUES (?,?,?,?,?,?)",
            (datetime.now().isoformat(), lat, lon, area_name, conf, img_path)
        )
        conn.commit()
        conn.close()

        # Push to Firebase for web UI
        self._push_to_firebase(lat, lon, area_name, conf)

        self.detection_count += 1
        print(f"  Saved: {area_name} | Conf: {conf:.2f} | Total: {self.detection_count}")

    def _process_detection(self, frame, conf, gps_poller):
        """Background thread: get location, save detection."""
        name, lat, lon = self._get_location(gps_poller)
        print(f"  Location: {name}")
        self._save_detection(lat, lon, name, conf, frame)

    def run(self):
        """Main entry point — starts ADB GPS, camera, and detection loop."""

        # ── Step 1: Check ADB connection ──
        print("\nChecking phone USB connection...")
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
            devices = [l for l in result.stdout.strip().split('\n')[1:] if l.strip() and 'device' in l]
            if not devices:
                print("ERROR: No phone found via USB!")
                print("  1. Connect phone via USB cable")
                print("  2. Enable USB Debugging:")
                print("     Settings → About phone → tap 'Build number' 7 times")
                print("     Settings → Developer options → USB debugging → ON")
                print("  3. Allow USB debugging on phone popup")
                return
            device_id = devices[0].split('\t')[0]
            print(f"  Phone connected: {device_id}")
        except FileNotFoundError:
            print("ERROR: ADB not found! Install Android platform-tools.")
            return

        # ── Step 2: Start ADB GPS poller ──
        print("  Starting GPS via ADB (USB)...")
        gps_poller = ADBGPSPoller(poll_interval=2.0)

        # Wait briefly for first GPS reading
        for _ in range(5):
            lat, lon, acc = gps_poller.get()
            if lat is not None:
                break
            time.sleep(1)

        lat, lon, acc = gps_poller.get()
        if lat is not None:
            name = self._reverse_geocode(lat, lon)
            with self._location_lock:
                self._current_display_location = name
            print(f"  GPS locked! Location: {name}")
            print(f"  Coordinates: {lat:.6f}, {lon:.6f} (accuracy: {acc:.0f}m)")
        elif self.manual_location:
            print(f"  GPS not available yet. Using: {self.manual_location}")
        else:
            print("  GPS acquiring signal... will update when available.")

        # ── Step 3: Show status ──
        print(f"\n{'='*58}")
        print(f"  POTHOLE TRACKER - ACTIVE")
        print(f"{'='*58}")
        print(f"  Camera : {self.phone_url}")
        print(f"  GPS    : USB (ADB) - automatic")
        with self._location_lock:
            loc = self._current_display_location
        if loc:
            print(f"  Location: {loc}")
        print(f"{'='*58}")

        # ── Step 4: Start camera ──
        grabber = FrameGrabber(self.snapshot_url)
        print("\nWaiting for camera feed from IP Webcam...")

        for _ in range(30):
            ok, _ = grabber.read()
            if ok:
                break
            time.sleep(0.5)
        else:
            print("ERROR: No camera frames. Check IP Webcam is running.")
            print(f"  Expected at: {self.snapshot_url}")
            gps_poller.stop()
            grabber.stop()
            return

        print("Camera connected!")
        print("\nTracker running! Press 'q' to quit.\n")

        # ── Step 5: Detection loop ──
        try:
            while True:
                ret, frame = grabber.read()
                if not ret:
                    time.sleep(0.05)
                    continue

                # Resize for faster inference
                h, w = frame.shape[:2]
                if w > 640:
                    scale = 640 / w
                    frame = cv2.resize(frame, (640, int(h * scale)))

                # YOLO detection
                results = self.model(frame, conf=self.conf_threshold, verbose=False)
                result = results[0]

                # Check for potholes
                if len(result.boxes) > 0:
                    now = time.time()
                    if now - self.last_detection_time > self.cooldown_sec:
                        best_conf = max(float(b.conf) for b in result.boxes)
                        if best_conf >= self.conf_threshold:
                            print(f"\n!! Pothole detected (Conf: {best_conf:.2f})")
                            annotated = result.plot().copy()
                            threading.Thread(
                                target=self._process_detection,
                                args=(annotated, best_conf, gps_poller),
                                daemon=True
                            ).start()
                            self.last_detection_time = now

                # Display frame with location + GPS overlay
                disp = result.plot()

                # Location name overlay (top)
                with self._location_lock:
                    loc_text = self._current_display_location
                if loc_text:
                    label = loc_text if len(loc_text) <= 60 else loc_text[:57] + "..."
                    cv2.putText(disp, label, (10, 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
                else:
                    cv2.putText(disp, "GPS: acquiring...", (10, 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

                # GPS accuracy + detection count (bottom)
                lat, lon, acc = gps_poller.get()
                gps_info = f"GPS: {acc:.0f}m accuracy" if acc else "GPS: no signal"
                cv2.putText(disp, f"{gps_info} | Detections: {self.detection_count}",
                            (10, disp.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

                cv2.imshow("Pothole Tracker", disp)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except KeyboardInterrupt:
            print("\nStopping tracker...")
        finally:
            gps_poller.stop()
            grabber.stop()
            cv2.destroyAllWindows()
            print(f"\nSession complete. {self.detection_count} potholes detected.")


# ═══════════════════════════════════════════════════════════════════════
#  Auto-detect phone IP via ADB
# ═══════════════════════════════════════════════════════════════════════

def _auto_detect_phone_ip():
    """Find the phone's IP address via ADB and test for IP Webcam on port 8080."""
    print("Auto-detecting phone IP via ADB...")
    try:
        result = subprocess.run(
            ['adb', 'shell', 'ip', 'route'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return None

        # Extract all 'src X.X.X.X' IPs from route table
        ips = re.findall(r'src\s+([\d.]+)', result.stdout)
        if not ips:
            return None

        # Test each IP for IP Webcam on port 8080
        for ip in ips:
            try:
                resp = requests.get(f"http://{ip}:8080/shot.jpg", timeout=2)
                if resp.status_code == 200:
                    print(f"  Found IP Webcam at: {ip}")
                    return ip
            except Exception:
                continue

        # If no IP Webcam found, return first IP (hotspot IP)
        print(f"  Phone IP: {ips[0]} (IP Webcam not detected — start the app)")
        return ips[0]
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════
#  CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Real-Time Dashcam Pothole Tracker (USB GPS via ADB)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dashcam_tracker.py                  (auto-detect phone IP)
  python dashcam_tracker.py --ip 10.42.106.44
  python dashcam_tracker.py --conf 0.6 --cooldown 5

Setup:
  1. Connect phone via USB with USB Debugging ON
  2. Start IP Webcam app on phone
  3. Run: python dashcam_tracker.py
        """
    )
    parser.add_argument("--ip", type=str, default=None,
                        help="Phone IP (auto-detected if not provided)")
    parser.add_argument("--model", type=str, default="runs/detect/train/weights/best.pt",
                        help="Path to YOLO model weights")
    parser.add_argument("--conf", type=float, default=0.5,
                        help="Detection confidence threshold (default: 0.5)")
    parser.add_argument("--cooldown", type=float, default=3.0,
                        help="Seconds between detections (default: 3)")
    parser.add_argument("--location", type=str, default=None,
                        help="Fallback location name if GPS unavailable")
    args = parser.parse_args()

    # Auto-detect phone IP if not provided
    phone_ip = args.ip
    if not phone_ip:
        phone_ip = _auto_detect_phone_ip()
        if not phone_ip:
            print("ERROR: Could not detect phone IP.")
            print("  Make sure phone is connected via USB with USB Debugging ON.")
            print("  Or provide manually: python dashcam_tracker.py --ip <phone_ip>")
            sys.exit(1)

    # Find model
    model_path = args.model
    if not os.path.exists(model_path):
        for alt in ["best.pt", "yolov8n.pt"]:
            if os.path.exists(alt):
                model_path = alt
                break
    if not os.path.exists(model_path):
        print(f"Model not found: {args.model}")
        sys.exit(1)

    DashcamTracker(
        phone_ip=phone_ip,
        model_path=model_path,
        conf_threshold=args.conf,
        cooldown_sec=args.cooldown,
        manual_location=args.location
    ).run()
