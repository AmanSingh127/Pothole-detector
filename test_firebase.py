import requests

FIREBASE_URL = "https://roadsentinel-87fc3-default-rtdb.asia-southeast1.firebasedatabase.app"

data = {
    "lat": 30.877,
    "lng": 76.872,
    "severity": "minor",
    "location": "Test from Python tracker",
    "confidence": 0.85,
    "timestamp": {".sv": "timestamp"}
}

r = requests.post(f"{FIREBASE_URL}/potholes.json", json=data, timeout=5)
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")
