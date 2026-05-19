from ultralytics import YOLO
import os
import cv2
import numpy as np

# Change to the project directory
os.chdir(r'C:\Users\AMAN SINGH\pothole_dataset')

# Load the trained model
model = YOLO('runs/detect/train/weights/best.pt')

# Test images to try
test_images = [
    'dashcam_test.png',
    'dashcam3.jpg', 
    'dashcam_test_detect.png',
    'dashcam_test_detect_conf10.png'
]

for img_name in test_images:
    if os.path.exists(img_name):
        print(f"\n=== Testing: {img_name} ===")
        
        # Run detection with lower confidence to catch more
        results = model(img_name, conf=0.1)
        print(f'Detections found: {len(results[0].boxes)}')
        
        # Print detection details
        if len(results[0].boxes) > 0:
            for i, box in enumerate(results[0].boxes):
                conf = box.conf.item()
                xyxy = box.xyxy[0].tolist()
                print(f'  Pothole {i+1}: Conf={conf:.3f}, Box={xyxy}')
        
        # Save result
        save_name = f'result_{img_name}'
        results[0].save(filename=save_name)
        print(f'Saved: {save_name}')
    else:
        print(f"\n=== {img_name} not found ===")

print("\nDone! Check the result_*.jpg files for visualizations.")

