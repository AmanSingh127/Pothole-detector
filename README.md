# 🕳️ Pothole Detector

A complete pothole detection system using YOLOv8, supporting image, video, and webcam detection with both command-line and GUI interfaces.

## Features

- ✅ **Image Detection** - Detect potholes in single images
- ✅ **Video Detection** - Process video files frame by frame
- ✅ **Webcam Detection** - Real-time detection from webcam feed
- ✅ **GUI Interface** - User-friendly graphical interface
- ✅ **Command-Line Interface** - Scriptable detection for automation
- ✅ **Configurable Confidence** - Adjustable detection threshold
- ✅ **Batch Processing** - Process multiple files efficiently

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd pothole_dataset
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure you have a trained model:**
   - The system will look for models in this order:
     - `runs/detect/train/weights/best.pt` (default trained model)
     - `yolov8n.pt` (pre-trained YOLOv8 nano)
     - `best.pt` (any model named best.pt)

## Usage

### GUI Application (Recommended for beginners)

Launch the graphical interface:
```bash
python pothole_detector_gui.py
```

**Steps:**
1. Load your trained model (or use the default if available)
2. Adjust confidence threshold if needed
3. Click "Detect Image" to process an image
4. Click "Detect Video" to process a video file
5. Click "Webcam" for real-time detection
6. Save results using "Save Result" button

### Command-Line Interface

#### Detect potholes in an image:
```bash
python pothole_detector.py --source path/to/image.jpg --output result.jpg --show
```

#### Detect potholes in a video:
```bash
python pothole_detector.py --source path/to/video.mp4 --output result.mp4
```

#### Use webcam:
```bash
python pothole_detector.py --source webcam --output recording.mp4
```

#### Custom model and confidence:
```bash
python pothole_detector.py --source image.jpg --model path/to/model.pt --conf 0.5
```

### Command-Line Options

- `--source`: Input source (image path, video path, or "webcam")
- `--model`: Path to YOLO model file (.pt) - optional, auto-detects if not provided
- `--conf`: Confidence threshold (0-1, default: 0.25)
- `--output`: Output path for annotated image/video
- `--show`: Display results (for images/videos)
- `--camera`: Camera ID for webcam (default: 0)

## Training Your Own Model

If you haven't trained a model yet, use the provided training script:

```bash
python train.py
```

Make sure your `data.yaml` is properly configured with your dataset paths.

## Project Structure

```
pothole_dataset/
├── pothole_detector.py          # Main detection script (CLI)
├── pothole_detector_gui.py      # GUI application
├── train.py                      # Training script
├── detect_pothole.py            # Simple detection script
├── predict.py                    # Prediction script
├── data.yaml                     # Dataset configuration
├── requirements.txt              # Python dependencies
├── images/                       # Training/validation images
│   ├── train/
│   └── val/
├── labels/                       # YOLO format labels
│   ├── train/
│   └── val/
└── runs/                         # Training outputs and results
    └── detect/
        └── train/
            └── weights/
                └── best.pt      # Trained model (after training)
```

## Examples

### Example 1: Quick Image Detection
```bash
python pothole_detector.py --source test_image.jpg --output detected.jpg --show
```

### Example 2: Process Video with Custom Confidence
```bash
python pothole_detector.py --source road_video.mp4 --output detected_video.mp4 --conf 0.3
```

### Example 3: Webcam Detection
```bash
python pothole_detector.py --source webcam
```

### Example 4: Using Python API
```python
from pothole_detector import PotholeDetector

# Initialize detector
detector = PotholeDetector(model_path="runs/detect/train/weights/best.pt", conf_threshold=0.25)

# Detect in image
results = detector.detect_image("test.jpg", output_path="result.jpg", show=True)

# Process video
detector.detect_video("video.mp4", output_path="output.mp4")

# Webcam detection
detector.detect_webcam()
```

## Troubleshooting

### Model Not Found
- Ensure you have trained a model or have `yolov8n.pt` in the project directory
- Specify model path explicitly: `--model path/to/model.pt`

### Webcam Not Working
- Check camera permissions
- Try different camera ID: `--camera 1`
- Ensure no other application is using the camera

### Low Detection Accuracy
- Lower confidence threshold: `--conf 0.15`
- Retrain with more diverse data
- Ensure good lighting conditions in images/videos

### Out of Memory Errors
- Reduce batch size in training
- Process videos in smaller chunks
- Use smaller image size: `imgsz=416` in training

## Requirements

- Python 3.8+
- CUDA-capable GPU (recommended for training, optional for inference)
- Webcam (for webcam detection)

## License

This project is open source and available for educational and research purposes.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Acknowledgments

- Built with [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- Uses OpenCV for image/video processing
