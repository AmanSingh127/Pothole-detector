"""
Pothole Detector GUI - User-friendly interface for pothole detection
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import cv2
from PIL import Image, ImageTk
import threading
from ultralytics import YOLO
import numpy as np


class PotholeDetectorGUI:
    """GUI application for pothole detection"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Pothole Detector")
        self.root.geometry("1000x700")
        
        self.model = None
        self.model_path = None
        self.current_image = None
        self.current_results = None
        self.conf_threshold = 0.25
        
        self.setup_ui()
        self.load_default_model()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🕳️ Pothole Detector", 
                               font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Model selection frame
        model_frame = ttk.LabelFrame(main_frame, text="Model Settings", padding="10")
        model_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(model_frame, text="Model Path:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.model_path_var = tk.StringVar()
        model_entry = ttk.Entry(model_frame, textvariable=self.model_path_var, width=50)
        model_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        ttk.Button(model_frame, text="Browse", command=self.browse_model).grid(row=0, column=2, padx=5)
        ttk.Button(model_frame, text="Load Model", command=self.load_model).grid(row=0, column=3, padx=5)
        
        model_frame.columnconfigure(1, weight=1)
        
        # Confidence threshold
        ttk.Label(model_frame, text="Confidence Threshold:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.conf_var = tk.DoubleVar(value=0.25)
        conf_scale = ttk.Scale(model_frame, from_=0.1, to=1.0, variable=self.conf_var, 
                               orient=tk.HORIZONTAL, length=200)
        conf_scale.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.conf_label = ttk.Label(model_frame, text="0.25")
        self.conf_label.grid(row=1, column=2, padx=5)
        conf_scale.configure(command=lambda v: self.conf_label.config(text=f"{float(v):.2f}"))
        
        # Status label
        self.status_label = ttk.Label(model_frame, text="Status: No model loaded", 
                                      foreground="red")
        self.status_label.grid(row=2, column=0, columnspan=4, pady=5, sticky=tk.W)
        
        # Control buttons frame
        control_frame = ttk.LabelFrame(main_frame, text="Detection Controls", padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        ttk.Button(control_frame, text="📷 Detect Image", 
                  command=self.detect_image, width=20).pack(pady=5)
        ttk.Button(control_frame, text="🎥 Detect Video", 
                  command=self.detect_video, width=20).pack(pady=5)
        ttk.Button(control_frame, text="📹 Webcam", 
                  command=self.detect_webcam, width=20).pack(pady=5)
        ttk.Button(control_frame, text="💾 Save Result", 
                  command=self.save_result, width=20).pack(pady=5)
        
        # Image display frame
        display_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        display_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), 
                          padx=5, pady=5)
        display_frame.columnconfigure(0, weight=1)
        display_frame.rowconfigure(0, weight=1)
        
        # Canvas for image display
        self.canvas = tk.Canvas(display_frame, bg="gray", width=600, height=400)
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar = ttk.Scrollbar(display_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Detection Results", padding="10")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.results_text = tk.Text(results_frame, height=5, width=80)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)
    
    def load_default_model(self):
        """Try to load default model paths"""
        possible_paths = [
            "runs/detect/train/weights/best.pt",
            "yolov8n.pt",
            "best.pt"
        ]
        for path in possible_paths:
            if Path(path).exists():
                self.model_path_var.set(path)
                self.load_model()
                break
    
    def browse_model(self):
        """Browse for model file"""
        filename = filedialog.askopenfilename(
            title="Select Model File",
            filetypes=[("PyTorch Model", "*.pt"), ("All Files", "*.*")]
        )
        if filename:
            self.model_path_var.set(filename)
    
    def load_model(self):
        """Load the YOLO model"""
        model_path = self.model_path_var.get()
        if not model_path or not Path(model_path).exists():
            messagebox.showerror("Error", "Model file not found!")
            return
        
        try:
            self.model = YOLO(model_path)
            self.model_path = model_path
            self.status_label.config(text=f"Status: Model loaded ({Path(model_path).name})", 
                                   foreground="green")
            self.update_results("✅ Model loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model:\n{e}")
            self.status_label.config(text="Status: Model load failed", foreground="red")
    
    def detect_image(self):
        """Detect potholes in an image"""
        if not self.model:
            messagebox.showwarning("Warning", "Please load a model first!")
            return
        
        filename = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.tiff *.avif"), 
                      ("All Files", "*.*")]
        )
        if not filename:
            return
        
        try:
            self.conf_threshold = self.conf_var.get()
            results = self.model(filename, conf=self.conf_threshold, verbose=False)
            result = results[0]
            
            # Get annotated image
            annotated = result.plot()
            self.current_image = annotated
            self.current_results = result
            
            # Display image
            self.display_image(annotated)
            
            # Update results
            num_detections = len(result.boxes)
            detections_info = []
            for i, box in enumerate(result.boxes):
                conf = float(box.conf.item())
                xyxy = [int(x) for x in box.xyxy[0].tolist()]
                detections_info.append(f"  #{i+1}: Confidence={conf:.3f}, BBox={xyxy}")
            
            results_text = f"Image: {Path(filename).name}\n"
            results_text += f"Detections: {num_detections}\n"
            if detections_info:
                results_text += "\n".join(detections_info)
            else:
                results_text += "No potholes detected."
            
            self.update_results(results_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Detection failed:\n{e}")
    
    def detect_video(self):
        """Detect potholes in a video"""
        if not self.model:
            messagebox.showwarning("Warning", "Please load a model first!")
            return
        
        filename = filedialog.askopenfilename(
            title="Select Video",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv"), 
                      ("All Files", "*.*")]
        )
        if not filename:
            return
        
        output_path = filedialog.asksaveasfilename(
            title="Save Output Video",
            defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4"), ("AVI", "*.avi"), ("All Files", "*.*")]
        )
        if not output_path:
            return
        
        # Run in separate thread to avoid blocking UI
        thread = threading.Thread(target=self.process_video, args=(filename, output_path))
        thread.daemon = True
        thread.start()
        messagebox.showinfo("Processing", "Video processing started in background.\n"
                          "Check the console for progress.")
    
    def process_video(self, video_path, output_path):
        """Process video in background thread"""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_count = 0
            total_detections = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                results = self.model(frame, conf=self.conf_threshold, verbose=False)
                annotated = results[0].plot()
                writer.write(annotated)
                total_detections += len(results[0].boxes)
            
            cap.release()
            writer.release()
            
            self.root.after(0, lambda: messagebox.showinfo(
                "Complete", 
                f"Video processing complete!\n"
                f"Processed {frame_count} frames\n"
                f"Total detections: {total_detections}\n"
                f"Saved to: {output_path}"
            ))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Video processing failed:\n{e}"))
    
    def detect_webcam(self):
        """Detect potholes from webcam"""
        if not self.model:
            messagebox.showwarning("Warning", "Please load a model first!")
            return
        
        messagebox.showinfo("Webcam", "Starting webcam detection.\n"
                          "Press 'q' to quit in the webcam window.")
        
        # Run webcam in separate thread
        thread = threading.Thread(target=self.run_webcam)
        thread.daemon = True
        thread.start()
    
    def run_webcam(self):
        """Run webcam detection"""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.root.after(0, lambda: messagebox.showerror("Error", "Could not open webcam!"))
                return
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                results = self.model(frame, conf=self.conf_threshold, verbose=False)
                annotated = results[0].plot()
                
                num_detections = len(results[0].boxes)
                cv2.putText(annotated, f"Detections: {num_detections}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(annotated, "Press 'q' to quit", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow("Pothole Detection - Webcam", annotated)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Webcam error:\n{e}"))
    
    def display_image(self, image):
        """Display image on canvas"""
        # Convert BGR to RGB
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        # Resize if too large
        max_width = 800
        max_height = 600
        height, width = image_rgb.shape[:2]
        
        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image_rgb = cv2.resize(image_rgb, (new_width, new_height))
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)
        photo = ImageTk.PhotoImage(image=pil_image)
        
        # Update canvas
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo  # Keep a reference
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def save_result(self):
        """Save current detection result"""
        if self.current_image is None:
            messagebox.showwarning("Warning", "No detection result to save!")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Detection Result",
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("All Files", "*.*")]
        )
        if filename:
            cv2.imwrite(filename, self.current_image)
            messagebox.showinfo("Success", f"Image saved to:\n{filename}")
    
    def update_results(self, text):
        """Update results text area"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, text)


def main():
    """Run the GUI application"""
    root = tk.Tk()
    app = PotholeDetectorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
