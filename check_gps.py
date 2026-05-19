"""
Quick diagnostic to check what GPS data the phone is sending.
Run this while IP Webcam is active on your phone.
"""
import requests
import json
import sys

phone_ip = sys.argv[1] if len(sys.argv) > 1 else "10.42.106.44"
clean_ip = phone_ip.replace("http://", "").replace("https://", "").split(":")[0]
base_url = f"http://{clean_ip}:8080"

# All possible GPS-related endpoints in IP Webcam
endpoints = [
    "/sensors.json",
    "/gps.json", 
    "/sensors.json?sense=gps",
    "/status.json",
]

print(f"Checking GPS endpoints on {base_url}")
print("=" * 60)

for ep in endpoints:
    url = base_url + ep
    print(f"\nTrying: {url}")
    try:
        resp = requests.get(url, timeout=3)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                formatted = json.dumps(data, indent=2)
                if len(formatted) > 2000:
                    formatted = formatted[:2000] + "\n... (truncated)"
                print(f"   Response:\n{formatted}")
            except:
                text = resp.text[:500]
                print(f"   Raw text: {text}")
        else:
            print(f"   Body: {resp.text[:200]}")
    except Exception as e:
        print(f"   ERROR: {e}")

print("\n" + "=" * 60)
print("\nIMPORTANT: Make sure you have done the following in IP Webcam app:")
print("   1. Go to 'Data logging' and enable it")
print("   2. Make sure phone Location/GPS is turned ON")
print("   3. Grant Location permission to IP Webcam app")
print("   4. Restart the IP Webcam server after enabling GPS")
