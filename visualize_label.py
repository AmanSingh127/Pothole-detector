import cv2
from pathlib import Path

img_path = r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_potholes_only\images\India_000011.jpg"
lbl_path = r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_potholes_only\labels\India_000011.txt"

# Load image
img = cv2.imread(img_path)
h, w = img.shape[:2]

# Draw labels
with open(lbl_path, 'r') as f:
    for line in f.readlines():
        parts = line.strip().split()
        if len(parts) == 5:
            cls, x, y, box_w, box_h = map(float, parts)
            # Convert YOLO to pixel coordinates
            x1 = int((x - box_w/2) * w)
            y1 = int((y - box_h/2) * h)
            x2 = int((x + box_w/2) * w)
            y2 = int((y + box_h/2) * h)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

# Save visualization
cv2.imwrite("debug_label.jpg", img)
print("✅ Visualization saved as debug_label.jpg")