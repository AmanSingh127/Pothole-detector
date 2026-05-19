import argparse

from ultralytics import YOLO


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=str, default="yolov8n.pt")
    ap.add_argument("--data", type=str, default="C:/Users/AMAN SINGH/pothole_dataset/roboflow_pothole_clean/data_pothole.yaml")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--name", type=str, default="yolov8n_roboflow_pothole_clean")
    args = ap.parse_args()

    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project="runs_pothole",
        name=args.name,
    ) 


if __name__ == "__main__":
    main()

