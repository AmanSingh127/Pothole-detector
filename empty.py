from pathlib import Path

lbl_dir = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\labels")
empty_count = 0
invalid_empty = 0

for lbl in lbl_dir.glob("*.txt"):
    with open(lbl, 'r') as f:
        content = f.read()
    
    if content.strip() == "":
        empty_count += 1
    else:
        # Check if non-empty files are valid
        lines = content.strip().split('\n')
        valid = True
        for line in lines:
            parts = line.split()
            if len(parts) != 5:
                valid = False
                break
            try:
                cls = int(parts[0])
                coords = [float(x) for x in parts[1:]]
                if cls != 0 or not all(0 <= c <= 1 for c in coords):
                    valid = False
                    break
            except:
                valid = False
                break
        if not valid:
            invalid_empty += 1

print(f"Empty label files: {empty_count}")
print(f"Invalid non-empty files: {invalid_empty}")