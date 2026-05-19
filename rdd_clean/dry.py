# dry_clean.py
from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # fresh start
model.train(
    data="data.yaml",
    epochs=1,
    imgsz=640,
    batch=8,
    workers=0,
    name="rdd_clean",
    verbose=True
)