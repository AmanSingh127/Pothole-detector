from ultralytics import YOLO
import argparse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=10, help="Quick check: try 5-10 first, then increase.")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument(
        "--fraction",
        type=float,
        default=1.0,
        help="Train on a fraction of data for a fast smoke test (e.g. 0.2).",
    )
    ap.add_argument("--model", type=str, default="yolov8n.pt")
    ap.add_argument("--name", type=str, default="yolov8n_rdd2022_balanced")
    args = ap.parse_args() 

    model = YOLO(args.model)  # fast baseline; switch to yolov8s.pt if you have GPU headroom
    model.train(
        data="C:/Users/AMAN SINGH/pothole_dataset/rdd2022_balanced.yaml",
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        fraction=args.fraction,
        project="runs_pothole",
        name=args.name,
    )


if __name__ == "__main__":
    main()

