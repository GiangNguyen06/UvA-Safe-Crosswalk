import cv2
import time
import torch
from ultralytics import YOLO

# 1. Configuration
MODELS = ['yolov8n.pt', 'yolov8m.pt', 'yolo11n.pt', 'yolo11m.pt']
VIDEOS = ['video1.mp4', 'video2.mp4'] # Add your video filenames here
TARGET_CLASSES = [0, 1, 2, 3, 5, 7]

def run_benchmark():
    results_table = []

    for model_name in MODELS:
        print(f"\n--- Loading Model: {model_name} ---")
        model = YOLO(model_name)
        if torch.cuda.is_available():
            model.to('cuda')

        for video_path in VIDEOS:
            cap = cv2.VideoCapture(video_path)
            total_time = 0
            frame_count = 0
            total_detections = 0

            print(f"Testing on {video_path}...")

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret or frame_count > 100: # Test first 100 frames for speed
                    break
                
                # Measure math time only
                start = time.time()
                results = model(frame, verbose=False, classes=TARGET_CLASSES)
                end = time.time()

                total_time += (end - start)
                total_detections += len(results[0].boxes)
                frame_count += 1

            avg_fps = frame_count / total_time
            avg_ms = (total_time / frame_count) * 1000
            
            results_table.append({
                "Model": model_name,
                "Video": video_path,
                "Avg FPS": round(avg_fps, 2),
                "Latency (ms)": round(avg_ms, 2),
                "Total Objects Found": total_detections
            })
            cap.release()

    # 3. Print the Final Report
    print("\n" + "="*50)
    print(f"{'Model':<12} | {'Video':<12} | {'FPS':<6} | {'Objects'}")
    print("-" * 50)
    for res in results_table:
        print(f"{res['Model']:<12} | {res['Video']:<12} | {res['Avg FPS']:<6} | {res['Total Objects Found']}")

if __name__ == "__main__":
    run_benchmark()