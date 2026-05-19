from ultralytics import YOLO

model = YOLO("yolov8n.pt")
model.train(
    data="C:/Users/AMAN SINGH/pothole_dataset/data.yaml",
    epochs=50,
    imgsz=640,
    batch=16
)
