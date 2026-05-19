from ultralytics import YOLO
import cv2

# Load your trained model
model = YOLO("runs/detect/train/weights/best.pt")

# Path to your video
video_path = "Video Project.mp4"

# Open video file
cap = cv2.VideoCapture(video_path)

# Get video properties
fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"📹 Video info: {width}x{height} @ {fps}fps, {total_frames} frames")

# Output video writer - using AVI format with XVID codec
output_path = "Video Project_detected.avi"
fourcc = cv2.VideoWriter_fourcc(*'XVID')
writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

frame_count = 0
total_detections = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Run detection with confidence threshold
        results = model(frame, conf=0.1, verbose=False)
        result = results[0]
        
        num_detections = len(result.boxes)
        total_detections += num_detections
        
        # Get annotated frame with bounding boxes
        annotated_frame = result.plot()
        
        # Add text overlay
        info_text = f"Frame: {frame_count}/{total_frames} | Detections: {num_detections}"
        cv2.putText(annotated_frame, info_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Write to output video
        writer.write(annotated_frame)
        
        # Print frame progress every 30 frames
        if frame_count % 30 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"⏳ Progress: {progress:.1f}% ({frame_count}/{total_frames}) - Detections: {num_detections}")

finally:
    cap.release()
    writer.release()

avg_detections = total_detections / frame_count if frame_count > 0 else 0

print(f"\n✅ Video processing complete!")
print(f"   Processed {frame_count} frames")
print(f"   Total detections: {total_detections}")
print(f"   Avg detections/frame: {avg_detections:.2f}")
print(f"   Saved to: {output_path}")

