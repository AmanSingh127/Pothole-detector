import os
from pathlib import Path

# Paths
ann_dir = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\annotations")
lbl_dir = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\labels")
lbl_dir.mkdir(exist_ok=True)

# Process each XML annotation
for xml_file in ann_dir.glob("*.xml"):
    # Read XML
    with open(xml_file, 'r') as f:
        content = f.read()
    
    # Extract objects
    lines = []
    for line in content.split('\n'):
        if '<name>' in line and '</name>' in line:
            name = line.split('<name>')[1].split('</name>')[0]
            if name == 'D00':  # ONLY potholes
                # Get bounding box
                # You'll need to parse xmin, ymin, xmax, ymax from XML
                # For simplicity, let's assume you have a proper converter
                pass
    
    # ⚠️ Better: Use your original conversion script but ONLY for D00