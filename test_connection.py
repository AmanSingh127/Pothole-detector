"""
Quick diagnostic to test connectivity to IP Webcam app.
Run: python test_connection.py <phone_ip>
"""
import requests
import sys
import os
import socket
import subprocess

# Fix Windows encoding for emoji
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def test_connection(phone_ip):
    # Clean IP
    clean_ip = phone_ip.replace("http://", "").replace("https://", "")
    
    # Check if user provided port
    if ":" in clean_ip:
        ip_part, port_part = clean_ip.rsplit(":", 1)
        port = int(port_part)
        base_url = f"http://{ip_part}:{port_part}"
    else:
        ip_part = clean_ip
        port = 8080
        base_url = f"http://{clean_ip}:8080"

    print(f"[DIAG] Diagnosing connection to IP Webcam")
    print(f"   Input IP:  {phone_ip}")
    print(f"   Parsed IP: {ip_part}")
    print(f"   Port:      {port}")
    print(f"   Base URL:  {base_url}")
    print("=" * 60)

    # Step 1: Check if the IP is reachable (ping)
    print(f"\n[1] Pinging {ip_part}...")
    try:
        result = subprocess.run(
            ["ping", "-n", "2", "-w", "2000", ip_part],
            capture_output=True, text=True, timeout=10
        )
        if "TTL=" in result.stdout:
            print(f"   [OK] Phone is reachable via ping")
        else:
            print(f"   [FAIL] Phone is NOT reachable via ping")
            print(f"   -> Make sure your phone and PC are on the SAME Wi-Fi network")
            print(f"   -> Check the IP address shown in the IP Webcam app")
            # Show last few lines
            lines = result.stdout.strip().split('\n')
            for line in lines[-4:]:
                print(f"   > {line.strip()}")
    except Exception as e:
        print(f"   [WARN] Ping failed: {e}")

    # Step 2: Check if port is open (TCP connect)
    print(f"\n[2] Checking TCP connection to {ip_part}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip_part, port))
        sock.close()
        if result == 0:
            print(f"   [OK] Port {port} is OPEN - IP Webcam server is listening")
        else:
            print(f"   [FAIL] Port {port} is CLOSED - IP Webcam server may not be running")
            print(f"   -> Open IP Webcam app and tap 'Start server'")
            print(f"   -> Error code: {result}")
    except Exception as e:
        print(f"   [FAIL] TCP connect failed: {e}")

    # Step 3: Try to fetch the main page
    print(f"\n[3] Fetching IP Webcam main page at {base_url}...")
    try:
        resp = requests.get(base_url, timeout=5)
        print(f"   [OK] Got response (status {resp.status_code})")
        print(f"   Content length: {len(resp.text)} bytes")
    except requests.exceptions.ConnectTimeout:
        print(f"   [FAIL] Connection TIMED OUT - IP Webcam is not responding")
        print(f"   -> Verify the IP shown at the bottom of IP Webcam app")
    except requests.exceptions.ConnectionError as e:
        err_str = str(e)
        if "actively refused" in err_str.lower() or "10061" in err_str:
            print(f"   [FAIL] Connection REFUSED - server not running on this port")
        elif "timed out" in err_str.lower():
            print(f"   [FAIL] Connection TIMED OUT - wrong IP or network issue")
        else:
            print(f"   [FAIL] Connection error: {e}")
        print(f"   -> IP Webcam server is probably not running")
    except Exception as e:
        print(f"   [FAIL] Error: {e}")

    # Step 4: Try to fetch a snapshot
    snapshot_url = f"{base_url}/shot.jpg"
    print(f"\n[4] Fetching snapshot from {snapshot_url}...")
    try:
        resp = requests.get(snapshot_url, timeout=5)
        if resp.status_code == 200 and len(resp.content) > 1000:
            print(f"   [OK] Got snapshot! ({len(resp.content)} bytes)")
            print(f"   -> Connection is WORKING! You can run dashcam_tracker.py")
        elif resp.status_code == 200:
            print(f"   [WARN] Got response but it's very small ({len(resp.content)} bytes)")
            print(f"   -> Camera might not be active. Check IP Webcam is showing preview")
        else:
            print(f"   [FAIL] Status {resp.status_code}: {resp.text[:200]}")
    except requests.exceptions.ConnectTimeout:
        print(f"   [FAIL] Snapshot request TIMED OUT")
    except requests.exceptions.ConnectionError as e:
        print(f"   [FAIL] Connection error: {e}")
    except Exception as e:
        print(f"   [FAIL] Error: {e}")

    # Step 5: Try video feed
    video_url = f"{base_url}/video"
    print(f"\n[5] Checking video endpoint {video_url}...")
    try:
        resp = requests.get(video_url, timeout=5, stream=True)
        if resp.status_code == 200:
            chunk = next(resp.iter_content(chunk_size=1024))
            print(f"   [OK] Video stream is active ({len(chunk)} bytes received)")
        else:
            print(f"   [FAIL] Status {resp.status_code}")
        resp.close()
    except Exception as e:
        print(f"   [FAIL] Video error: {e}")

    print("\n" + "=" * 60)
    print("\n[CHECKLIST]")
    print("   [ ] Phone and PC on the SAME Wi-Fi network?")
    print("   [ ] IP Webcam app is OPEN and 'Server started' is shown?")
    print("   [ ] IP shown at bottom of IP Webcam matches what you entered?")
    print("   [ ] No VPN or firewall blocking port 8080?")
    print(f"   [ ] Try opening {base_url} in your PC browser to verify")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_connection.py <phone_ip>")
        print("Example: python test_connection.py 192.168.1.5")
        sys.exit(1)
    
    test_connection(sys.argv[1])
