# verify_label.py
import cv2
from pathlib import Path

# Pick one image from your rdd2022_clean/images/
img_path = r"C:\Users\AMAN SINGH\pothole_dataset\rdd2022_clean\images\India_000011.jpg"
lbl_path = r"C:\Users\AMAN SINGH\pothole_dataset\rdd2022_clean\labels\India_000011.txt"

img = cv2.imread(img_path)
h, w = img.shape[:2]

with open(lbl_path, 'r') as f:
    for line in f.readlines():
        parts = line.strip().split()
        if len(parts) == 5:
            cls, x, y, bw, bh = map(float, parts)
            # Convert to pixel coords
            x1 = int((x - bw/2) * w)
            y1 = int((y - bh/2) * h)
            x2 = int((x + bw/2) * w)
            y2 = int((y + bh/2) * h)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

cv2.imwrite("verified_label.jpg", img)
print("✅ Check 'verified_label.jpg' — does the red box surround a pothole?")