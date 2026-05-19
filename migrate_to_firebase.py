"""
Migrate SQLite pothole records to Firebase Realtime Database.
Only migrates records that have valid GPS coordinates.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import sqlite3
import requests
import time
import os

FIREBASE_DB_URL = "https://roadsentinel-87fc3-default-rtdb.asia-southeast1.firebasedatabase.app"
DB_PATH = "potholes.db"


def conf_to_severity(conf):
    if conf >= 0.8:
        return "severe"
    elif conf >= 0.6:
        return "moderate"
    return "minor"


def migrate():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Get records WITH GPS coordinates
    rows = conn.execute(
        "SELECT * FROM potholes WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY id"
    ).fetchall()
    
    print(f"Found {len(rows)} records with GPS to migrate")
    
    success = 0
    failed = 0
    
    for row in rows:
        data = {
            "lat": row["latitude"],
            "lng": row["longitude"],
            "severity": conf_to_severity(row["confidence"] or 0),
            "location": row["location_text"] or "Unknown Location",
            "confidence": round(row["confidence"] or 0, 2),
            "timestamp": int(time.mktime(time.strptime(row["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))) * 1000,
            "image_path": row["image_path"] or "",
            "source": "dashcam_tracker"
        }
        
        try:
            resp = requests.post(
                f"{FIREBASE_DB_URL}/potholes.json",
                json=data, timeout=5
            )
            if resp.status_code == 200:
                success += 1
                print(f"  [OK] ID {row['id']}: {data['location'][:40]} | {data['severity']} | {data['confidence']}")
            else:
                failed += 1
                print(f"  [FAIL] ID {row['id']}: HTTP {resp.status_code}")
        except Exception as e:
            failed += 1
            print(f"  [FAIL] ID {row['id']}: {e}")
    
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"  Migration Complete!")
    print(f"  Migrated: {success}")
    print(f"  Failed: {failed}")
    print(f"  Skipped (no GPS): {169 - len(rows)}")
    print(f"{'='*50}")


if __name__ == "__main__":
    migrate()
