from pathlib import Path
import shutil

# Source paths
src_img = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\images")
src_lbl = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\labels")

# Destination
dst = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_potholes_only")
(dst / "images").mkdir(parents=True, exist_ok=True)
(dst / "labels").mkdir(parents=True, exist_ok=True)

pothole_count = 0

for lbl in src_lbl.glob("*.txt"):
    # Check if label contains potholes
    with open(lbl, 'r') as f:
        if f.read().strip() != "":
            # Copy image and label
            img_path = src_img / f"{lbl.stem}.jpg"
            if img_path.exists():
                shutil.copy(img_path, dst / "images" / img_path.name)
                shutil.copy(lbl, dst / "labels" / lbl.name)
                pothole_count += 1

print(f"✅ Created pothole-only dataset: {pothole_count} images")