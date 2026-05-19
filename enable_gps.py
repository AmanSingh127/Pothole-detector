"""Try every known IP Webcam API to remotely enable GPS sensor"""
import requests
import sys
import time

ip = sys.argv[1] if len(sys.argv) > 1 else "10.42.106.44"
base = f"http://{ip}:8080"

# All known IP Webcam endpoints to enable GPS
endpoints = [
    "/enablesensor/gps/on",
    "/startsensor/gps",
    "/settings/gps?set=on",
    "/settings/sensor_gps?set=on",
    "/pref?type=bool&key=gps_active&value=true",
    "/pref?type=bool&key=sensor_gps&value=true",
    "/settings",
]

print(f"Trying to enable GPS on {base}...\n")

for ep in endpoints:
    url = base + ep
    try:
        resp = requests.get(url, timeout=3)
        preview = resp.text[:200].replace('\n', ' ')
        print(f"  {ep}")
        print(f"    Status: {resp.status_code} | Response: {preview}\n")
    except Exception as e:
        print(f"  {ep}")
        print(f"    ERROR: {e}\n")

# Now check if GPS started working
print("Checking GPS after enable attempts...")
time.sleep(2)
try:
    resp = requests.get(f"{base}/gps.json", timeout=3)
    data = resp.json()
    if data:
        print(f"  GPS data: {data}")
    else:
        print("  Still empty :(")
except Exception as e:
    print(f"  Error: {e}")
