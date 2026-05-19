# convert_rdd2022.py
import xml.etree.ElementTree as ET
from pathlib import Path
import cv2

# Define paths
ann_dir = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\annotations")
img_dir = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\images")
lbl_dir = Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india\train\labels")
lbl_dir.mkdir(exist_ok=True)

print(f"Processing {len(list(ann_dir.glob('*.xml')))} XML files...")

converted = 0
for xml_file in ann_dir.glob("*.xml"):
    img_file = img_dir / f"{xml_file.stem}.jpg"
    lbl_file = lbl_dir / f"{xml_file.stem}.txt"
    
    # Skip if image doesn't exist
    if not img_file.exists():
        continue
        
    # Read image to get dimensions
    try:
        img = cv2.imread(str(img_file))
        h, w = img.shape[:2]
    except:
        continue
    
    # Parse XML
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except:
        continue
    
    yolo_lines = []
    for obj in root.findall('object'):
        name_elem = obj.find('name')
        if name_elem is None:
            continue
        name = name_elem.text
        
        # ONLY keep D00 (potholes)
        if name != 'D00':
            continue
            
        # Get bounding box
        bndbox = obj.find('bndbox')
        if bndbox is None:
            continue
            
        try:
            xmin = int(bndbox.find('xmin').text)
            ymin = int(bndbox.find('ymin').text)
            xmax = int(bndbox.find('xmax').text)
            ymax = int(bndbox.find('ymax').text)
        except:
            continue
        
        # Validate coordinates
        if xmin >= xmax or ymin >= ymax or xmin < 0 or ymin < 0 or xmax > w or ymax > h:
            continue
        
        # Convert to YOLO format
        x_center = (xmin + xmax) / 2 / w
        y_center = (ymin + ymax) / 2 / h
        width = (xmax - xmin) / w
        height = (ymax - ymin) / h
        
        yolo_lines.append(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
    
    # Save label file (even if empty)
    with open(lbl_file, 'w') as f:
        f.writelines(yolo_lines)
    
    converted += 1
    if converted % 500 == 0:
        print(f"Converted {converted} files...")

print(f"✅ Conversion complete! Processed {converted} files.")
print(f"Labels saved to: {lbl_dir}")