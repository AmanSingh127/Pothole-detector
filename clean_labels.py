from pathlib import Path

# Path to your labels
lbl_dir = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\labels")

print(f"Cleaning {len(list(lbl_dir.glob('*.txt')))} label files...")

cleaned = 0
for lbl_file in lbl_dir.glob("*.txt"):
    with open(lbl_file, 'r') as f:
        lines = f.readlines()
    
    # Keep only lines that start with "0" and have 5 valid numbers
    new_lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 5:
            try:
                cls = int(parts[0])
                coords = list(map(float, parts[1:]))
                # Validate coordinates (0-1 range)
                if cls == 0 and all(0 <= c <= 1 for c in coords):
                    new_lines.append(line)
            except:
                continue
    
    # Save cleaned label
    with open(lbl_file, 'w') as f:
        f.writelines(new_lines)
    
    cleaned += 1
    if cleaned % 500 == 0:
        print(f"Cleaned {cleaned} files...")

print(f"✅ Cleaning complete! Processed {cleaned} files.")