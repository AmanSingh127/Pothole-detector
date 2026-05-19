from ultralytics import YOLO
import cv2

# Load your trained model
model = YOLO("runs/detect/train/weights/best.pt")

# Path to your image (change this to your test image)
image_path = "original.jpg"  # ← change this to your test image

# Run detection with lower confidence threshold to catch more potholes
# conf=0.1 means it will show detections with 10% confidence or higher
results = model(image_path, conf=0.1)

# Print detection details
print(f"Detections found: {len(results[0].boxes)}")
for i, box in enumerate(results[0].boxes):
    conf = box.conf.item()
    print(f"  Pothole {i+1}: Confidence = {conf:.3f}")

# Save and show result
results[0].save(filename="detected_pothole.jpg")  # saves with bounding box
print("✅ Detection complete! Check 'detected_pothole.jpg'")

# Optional: Show image (may not work in all terminals)
img = cv2.imread("detected_pothole.jpg")
cv2.imshow("Pothole Detection", img)
cv2.waitKey(0)
cv2.destroyAllWindows()