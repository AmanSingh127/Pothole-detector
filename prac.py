from pathlib import Path

lbl_dir = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\labels")
invalid_files = 0

for lbl in lbl_dir.glob("*.txt"):
    with open(lbl, 'r') as f:
        lines = f.readlines()
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 5:
            try:
                cls = int(parts[0])
                if cls != 0:  # Should only be class 0
                    invalid_files += 1
                    break
            except:
                invalid_files += 1
                break

print(f"Files with non-pothole classes: {invalid_files}")