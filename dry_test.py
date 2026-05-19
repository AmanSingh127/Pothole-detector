# pothole_dry_test.py
from ultralytics import YOLO

model = YOLO("yolov8n.pt")
model.train(
    data="pothole_only.yaml",
    epochs=1,
    imgsz=640,
    batch=8,
    workers=0,
    name="pothole_only_dry"
)