import os
import shutil
from pathlib import Path
import random

# Set seed for reproducibility
random.seed(42)

# Paths
src_img = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\images")
src_lbl = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\labels")

# Create val folders
val_img = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\val\images")
val_lbl = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\val\labels")
val_img.mkdir(parents=True, exist_ok=True)
val_lbl.mkdir(parents=True, exist_ok=True)

# Get all images
images = list(src_img.glob("*.jpg"))
print(f"Total images: {len(images)}")

# Shuffle and select 20% for validation
random.shuffle(images)
num_val = int(0.2 * len(images))
val_images = images[:num_val]

print(f"Moving {num_val} images to val...")

# Move images and labels
for img_path in val_images:
    # Move image
    shutil.move(str(img_path), str(val_img / img_path.name))
    # Move label
    lbl_path = src_lbl / f"{img_path.stem}.txt"
    if lbl_path.exists():
        shutil.move(str(lbl_path), str(val_lbl / f"{img_path.stem}.txt"))

print("✅ Train/val split completed!")