"""
Lightweight GPS Server — runs on your PC.
Open the URL shown in the console on your PHONE's browser.
The phone's browser shares precise GPS with this server.
The dashcam_tracker.py reads GPS from this server automatically.

Usage: python gps_server.py
Then open the displayed URL on your phone browser.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import socket
import sys
import os

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Shared GPS data
gps_data = {"lat": None, "lon": None, "accuracy": None, "timestamp": None}
gps_lock = threading.Lock()

GPS_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pothole Tracker GPS</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #0f172a; color: #e2e8f0;
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; padding: 16px;
  }
  .card {
    background: #1e293b; border-radius: 16px;
    padding: 32px; max-width: 400px; width: 100%;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    text-align: center;
  }
  h1 { font-size: 20px; margin-bottom: 8px; color: #38bdf8; }
  .subtitle { font-size: 13px; color: #94a3b8; margin-bottom: 24px; }
  .status {
    padding: 16px; border-radius: 12px;
    margin: 16px 0; font-size: 14px;
  }
  .status.waiting { background: #422006; border: 1px solid #f59e0b; }
  .status.active { background: #052e16; border: 1px solid #22c55e; }
  .status.error { background: #450a0a; border: 1px solid #ef4444; }
  .location { font-size: 13px; color: #94a3b8; margin-top: 12px; line-height: 1.6; }
  .location strong { color: #e2e8f0; }
  .pulse {
    display: inline-block; width: 10px; height: 10px;
    border-radius: 50%; margin-right: 6px; vertical-align: middle;
  }
  .pulse.green { background: #22c55e; animation: pulse 1.5s infinite; }
  .pulse.yellow { background: #f59e0b; animation: pulse 1.5s infinite; }
  .pulse.red { background: #ef4444; }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.3); }
  }
  .btn {
    background: #2563eb; color: white; border: none;
    padding: 12px 24px; border-radius: 8px;
    font-size: 15px; cursor: pointer; margin-top: 16px;
    width: 100%;
  }
  .btn:active { background: #1d4ed8; }
</style>
</head>
<body>
<div class="card">
  <h1>Pothole Tracker GPS</h1>
  <p class="subtitle">Keep this page open while driving</p>
  <div id="statusBox" class="status waiting">
    <span class="pulse yellow"></span> Waiting for GPS permission...
  </div>
  <div id="locationInfo" class="location"></div>
  <button class="btn" id="startBtn" onclick="startGPS()">Enable GPS</button>
</div>
<script>
let watchId = null;
let sendCount = 0;

function startGPS() {
  document.getElementById('startBtn').style.display = 'none';
  if (!navigator.geolocation) {
    showError("GPS not supported on this browser");
    return;
  }
  watchId = navigator.geolocation.watchPosition(onPosition, onError, {
    enableHighAccuracy: true,
    maximumAge: 2000,
    timeout: 10000
  });
}

function onPosition(pos) {
  const lat = pos.coords.latitude;
  const lon = pos.coords.longitude;
  const acc = pos.coords.accuracy;

  // Send to PC server
  fetch('/gps_update', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({lat: lat, lon: lon, accuracy: acc})
  }).then(() => {
    sendCount++;
    const box = document.getElementById('statusBox');
    box.className = 'status active';
    box.innerHTML = '<span class="pulse green"></span> GPS Active — Sending to PC';

    document.getElementById('locationInfo').innerHTML =
      '<strong>Lat:</strong> ' + lat.toFixed(6) + '<br>' +
      '<strong>Lon:</strong> ' + lon.toFixed(6) + '<br>' +
      '<strong>Accuracy:</strong> ' + acc.toFixed(0) + 'm<br>' +
      '<strong>Updates sent:</strong> ' + sendCount;
  }).catch(err => {
    showError("Can't reach PC: " + err.message);
  });
}

function onError(err) {
  showError(err.message);
}

function showError(msg) {
  const box = document.getElementById('statusBox');
  box.className = 'status error';
  box.innerHTML = '<span class="pulse red"></span> ' + msg;
}

// Auto-start
startGPS();
</script>
</body>
</html>"""


class GPSHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(GPS_PAGE.encode())

        elif self.path == '/gps':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with gps_lock:
                self.wfile.write(json.dumps(gps_data).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/gps_update':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                with gps_lock:
                    gps_data['lat'] = data['lat']
                    gps_data['lon'] = data['lon']
                    gps_data['accuracy'] = data.get('accuracy')
                    import time
                    gps_data['timestamp'] = time.time()
                print(f"\r📍 GPS: {data['lat']:.6f}, {data['lon']:.6f} (±{data.get('accuracy', '?')}m)   ", end='', flush=True)
            except Exception as e:
                print(f"\n⚠️ Bad GPS data: {e}")

            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'ok')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def get_local_ip():
    """Get the PC's local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


if __name__ == "__main__":
    PORT = 8085
    local_ip = get_local_ip()

    print("=" * 55)
    print("  📡 Pothole Tracker — GPS Server")
    print("=" * 55)
    print(f"\n  Open this URL on your PHONE's browser:\n")
    print(f"  👉  http://{local_ip}:{PORT}")
    print(f"\n  Keep the page open while driving.")
    print(f"  The dashcam tracker will read GPS from this server.")
    print("=" * 55)
    print("\n  Waiting for GPS data from phone...\n")

    server = HTTPServer(("0.0.0.0", PORT), GPSHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 GPS Server stopped.")
        server.server_close()
