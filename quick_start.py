"""
Quick Start Script - Simple example to get started with pothole detection
"""

from pothole_detector import PotholeDetector
from pathlib import Path

def main():
    print("🕳️ Pothole Detector - Quick Start\n")
    print("=" * 50)
    
    # Try to initialize detector
    try:
        print("\n1. Loading model...")
        detector = PotholeDetector()
        print("   ✅ Model loaded!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("\n   Please ensure you have a trained model.")
        print("   Run 'python train.py' to train a model first.")
        return
    
    # Example: Detect in an image
    print("\n2. Example: Image Detection")
    print("   To detect potholes in an image, use:")
    print("   python pothole_detector.py --source your_image.jpg --output result.jpg --show")
    
    # Example: Detect in a video
    print("\n3. Example: Video Detection")
    print("   To detect potholes in a video, use:")
    print("   python pothole_detector.py --source your_video.mp4 --output result.mp4")
    
    # Example: Webcam
    print("\n4. Example: Webcam Detection")
    print("   To use webcam, use:")
    print("   python pothole_detector.py --source webcam")
    
    # GUI option
    print("\n5. GUI Application")
    print("   For a user-friendly interface, run:")
    print("   python pothole_detector_gui.py")
    
    print("\n" + "=" * 50)
    print("\n✅ Quick start guide complete!")
    print("\n💡 Tip: Check README.md for detailed documentation")

if __name__ == "__main__":
    main()
