import cv2
from ultralytics import YOLO
import sqlite3
from datetime import datetime
import os

# -------------------------
# CONFIGURATION
# -------------------------
MODEL_PATH = "runs/detect/train/weights/best.pt"  # trained model (relative)
TEST_SOURCE = "original.jpg"  # test image (relative)

# Simulated "location-wise" name (no GPS needed!)
SIMULATED_LOCATION = "Near AIIMS Flyover, Ring Road, New Delhi"

# -------------------------
# INIT DATABASE
# -------------------------
def init_db():
    conn = sqlite3.connect("potholes.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS potholes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        location_text TEXT,
        confidence REAL,
        image_path TEXT
    )''')
    conn.commit()
    conn.close()

# -------------------------
# SAVE DETECTION
# -------------------------
def save_detection(location, conf, img_path):
    conn = sqlite3.connect("potholes.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO potholes (timestamp, location_text, confidence, image_path)
        VALUES (?, ?, ?, ?)
    """, (datetime.now().isoformat(), location, conf, img_path))
    conn.commit()
    conn.close()
    print(f"✅ Saved: {location} | Confidence: {conf:.2f}")

# -------------------------
# MAIN TEST
# -------------------------
def main():
    init_db()
    
    # Load model
    model = YOLO(MODEL_PATH)
    
    # Check if source is image or video
    if TEST_SOURCE.lower().endswith(('.jpg', '.jpeg', '.png')):
        # Process single image
        print("📸 Processing image...")
        results = model(TEST_SOURCE, conf=0.3, verbose=False)
        result = results[0]
        
        annotated = result.plot()
        output_path = "detected_output.jpg"
        cv2.imwrite(output_path, annotated)
        
        # Save all detections
        for box in result.boxes:
            conf = float(box.conf)
            if conf >= 0.4:
                save_detection(SIMULATED_LOCATION, conf, output_path)
        
        print(f"🎯 Found {len(result.boxes)} pothole(s)")
        cv2.imshow("Result", annotated)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    else:
        # Process video (if you have one)
        cap = cv2.VideoCapture(TEST_SOURCE)
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret: break
            frame_count += 1
            
            results = model(frame, conf=0.3, verbose=False)
            annotated = results[0].plot()
            
            for box in results[0].boxes:
                conf = float(box.conf)
                if conf >= 0.4:
                    save_detection(SIMULATED_LOCATION, conf, f"frame_{frame_count}.jpg")
            
            cv2.imshow("Video", annotated)
            if cv2.waitKey(1) == ord('q'): break
        
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()