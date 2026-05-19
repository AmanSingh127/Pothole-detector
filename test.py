from pothole_detector import PotholeDetector  # assuming your main script is named pothole_detector.py

# Initialize detector (uses best.pt automatically)
detector = PotholeDetector()

# Insert your image path HERE
image_path = r"C:\Users\AMAN SINGH\pothole_dataset\New pothole detection.v1i.yolov8\train\images\vlcsnap-2020-04-12-02h03m08s323_jpg.rf.073323847a92f40b848c2e80099b4491.jpg"

# Run detection
result = detector.detect_image(image_path, output_path="detected_output.jpg", show=True)
print(f"Found {result['num_detections']} potholes")