# copy_clean_data.py
import shutil
from pathlib import Path

src_img = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\images")
src_lbl = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\labels")
dst = Path(r"C:\Users\AMAN SINGH\pothole_dataset\rdd_clean")
(dst / "images").mkdir(parents=True, exist_ok=True)
(dst / "labels").mkdir(parents=True, exist_ok=True)

count = 0
for lbl in src_lbl.glob("*.txt"):
    if lbl.read_text().strip():
        img = src_img / f"{lbl.stem}.jpg"
        if img.exists():
            shutil.copy(img, dst / "images" / img.name)
            shutil.copy(lbl, dst / "labels" / lbl.name)
            count += 1

print(f"Copied {count} pothole images + labels to rdd2022_clean/")
