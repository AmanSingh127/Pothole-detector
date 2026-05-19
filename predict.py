# test_single_image.py
from ultralytics import YOLO
import cv2

# 🔹 Step 1: Load your PROVEN model (the one that works on images)
model_path = r"C:\Users\AMAN SINGH\pothole_dataset\runs\detect\train\weights\best.pt"
print(f"Loading model: {model_path}")
model = YOLO(model_path)

# 🔹 Step 2: Load your dashcam image
image_path = r"C:\Users\AMAN SINGH\pothole_dataset\thumb.jpg"
print(f"Loading image: {image_path}")

# 🔹 Step 3: Run inference (1 epoch = 1 forward pass)
print("🔍 Running inference...")
results = model(image_path, imgsz=640, conf=0.25, verbose=False)

# 🔹 Step 4: Analyze detections
result = results[0]
num_detections = len(result.boxes)
print(f"\n📊 Detection Summary:")
print(f"   Total boxes: {num_detections}")

if num_detections > 0:
    for i, box in enumerate(result.boxes):
        cls = int(box.cls.item())
        conf = float(box.conf.item())
        xyxy = [int(x) for x in box.xyxy[0].tolist()]
        print(f"   #{i+1}: class={cls} (pothole), conf={conf:.3f}, bbox={xyxy}")
else:
    print("   ❌ No detections")

# 🔹 Step 5: Save annotated image
output_path = "detected_debug.jpg"
result.save(filename=output_path)
print(f"\n📸 Annotated image saved to: {output_path}")

# 🔹 Optional: Display (works in most IDEs)
try:
    img = cv2.imread(output_path)
    if img is not None:
        cv2.imshow("Pothole Detection Test", img)
        print("Press any key to close window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
except Exception as e:
    print(f"⚠️ OpenCV display failed (normal on some systems): {e}")

print("\n✅ Script completed. Did you see a red box around the pothole?")