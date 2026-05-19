"""
Pothole Detector - Complete Detection System
Supports images, videos, and webcam input
"""

import cv2
import argparse
from pathlib import Path
from ultralytics import YOLO
import numpy as np
from typing import Optional, Tuple


class PotholeDetector:
    """Main pothole detection class"""
    
    def __init__(self, model_path: str = None, conf_threshold: float = 0.25):
        """
        Initialize the pothole detector
        
        Args:
            model_path: Path to trained YOLO model (.pt file)
            conf_threshold: Confidence threshold for detections (0-1)
        """
        # Try to find the best model if not provided
        if model_path is None:
            possible_paths = [
                "runs/detect/new_pothole_model/weights/best.pt",  # Your new training
                "runs/detect/train/weights/best.pt",              # Original Kaggle model
                "best.pt",
                "yolov8n.pt"
            ]
            for path in possible_paths:
                if Path(path).exists():
                    model_path = path
                    break
        
        if model_path is None or not Path(model_path).exists():
            raise FileNotFoundError(
                f"Model not found. Please train a model first.\n"
                f"Tried paths: {possible_paths}"
            )
        
        print(f"✅ Loading model from: {model_path}")
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        print("🚀 Model loaded successfully!")

    def detect_image(self, image_path: str, output_path: str = None, 
                     show: bool = False) -> dict:
        """
        Detect potholes in a single image
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        print(f"🔍 Processing image: {image_path}")
        results = self.model(image_path, conf=self.conf_threshold, verbose=False)
        result = results[0]
        
        # Extract detection information
        detections = []
        for box in result.boxes:
            cls = int(box.cls.item())
            conf = float(box.conf.item())
            xyxy = box.xyxy[0].tolist()
            detections.append({
                'class': cls,
                'confidence': conf,
                'bbox': xyxy
            })
        
        # Save annotated image
        if output_path:
            result.save(filename=output_path)
            print(f"✅ Saved annotated image to: {output_path}")
        
        # Display if requested
        if show:
            annotated = result.plot()
            cv2.imshow("Pothole Detection", annotated)
            print("Press any key to close...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        summary = {
            'image_path': image_path,
            'num_detections': len(detections),
            'detections': detections
        }
        
        print(f"🎯 Found {len(detections)} pothole(s)")
        return summary
    
    def detect_video(self, video_path: str, output_path: str = None,
                     show: bool = False) -> None:
        """Detect potholes in a video file"""
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        print(f"🎥 Processing video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"📹 Video info: {width}x{height} @ {fps}fps, {total_frames} frames")
        
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        total_detections = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                results = self.model(frame, conf=self.conf_threshold, verbose=False)
                result = results[0]
                num_detections = len(result.boxes)
                total_detections += num_detections
                
                annotated_frame = result.plot()
                info_text = f"Frame: {frame_count}/{total_frames} | Detections: {num_detections}"
                cv2.putText(annotated_frame, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if writer:
                    writer.write(annotated_frame)
                
                if show:
                    cv2.imshow("Pothole Detection", annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                if frame_count % 30 == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"⏳ Progress: {progress:.1f}% ({frame_count}/{total_frames})")
        
        finally:
            cap.release()
            if writer:
                writer.release()
            if show:
                cv2.destroyAllWindows()
        
        avg_detections = total_detections / frame_count if frame_count > 0 else 0
        print(f"\n✅ Video processing complete!")
        print(f"   Processed {frame_count} frames")
        print(f"   Total detections: {total_detections}")
        print(f"   Avg detections/frame: {avg_detections:.2f}")
        if output_path:
            print(f"   Saved to: {output_path}")
    
    def detect_webcam(self, camera_id: int = 0, output_path: str = None) -> None:
        """Detect potholes from webcam feed"""
        print(f"📹 Starting webcam (Camera {camera_id}). Press 'q' to quit.")
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open camera {camera_id}")
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                results = self.model(frame, conf=self.conf_threshold, verbose=False)
                result = results[0]
                annotated_frame = result.plot()
                
                num_detections = len(result.boxes)
                cv2.putText(annotated_frame, f"Detections: {num_detections}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(annotated_frame, "Press 'q' to quit", (10, height - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                if writer:
                    writer.write(annotated_frame)
                
                cv2.imshow("Pothole Detection - Webcam", annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        finally:
            cap.release()
            if writer:
                writer.release()
            cv2.destroyAllWindows()
        
        print(f"\n✅ Webcam session ended. Processed {frame_count} frames.")


def main():
    parser = argparse.ArgumentParser(description="Pothole Detection System")
    parser.add_argument("--model", type=str, default=None,
                       help="Path to trained YOLO model (.pt file)")
    parser.add_argument("--conf", type=float, default=0.25,
                       help="Confidence threshold (0-1)")
    parser.add_argument("--source", type=str, required=True,
                       help="Input source: path to image/video, or 'webcam'")
    parser.add_argument("--output", type=str, default=None,
                       help="Output path for annotated image/video")
    parser.add_argument("--show", action="store_true",
                       help="Display results")
    parser.add_argument("--camera", type=int, default=0,
                       help="Camera ID (default: 0)")
    
    args = parser.parse_args()
    
    try:
        detector = PotholeDetector(model_path=args.model, conf_threshold=args.conf)
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    try:
        if args.source.lower() == "webcam":
            detector.detect_webcam(camera_id=args.camera, output_path=args.output)
        elif Path(args.source).is_file():
            ext = Path(args.source).suffix.lower()
            if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                detector.detect_image(args.source, output_path=args.output, show=args.show)
            elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                detector.detect_video(args.source, output_path=args.output, show=args.show)
            else:
                print(f"❌ Unsupported file format: {ext}")
        else:
            print(f"❌ Source not found: {args.source}")
    except Exception as e:
        print(f"❌ Detection error: {e}")


if __name__ == "__main__":
    main()