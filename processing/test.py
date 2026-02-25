import cv2
import time
from detector import CrosswalkDetector

def test_on_video(video_path):
    # Initialize your same AI detector
    detector = CrosswalkDetector()
    
    # Open the local video file
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    # --- FIXED ATTRIBUTE NAMES ---
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) # Total length
    video_fps = cap.get(cv2.CAP_PROP_FPS)                # Video speed
    
    print(f"[INFO] Testing AI on: {video_path}")
    print(f"[INFO] Video Length: {total_frames} frames")
    print(f"[INFO] Video Original FPS: {video_fps}")

    prev_time = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("[INFO] End of video reached.")
            break 
            
        # --- TIMER START ---
        start_time = time.time()

        # Use your EXACT same processing logic from detector.py
        processed_frame = detector.process_frame(frame)
        
        # --- CALCULATE REAL-TIME FPS ---
        # This is how fast your RTX 2070 is actually processing
        end_time = time.time()
        inference_fps = 1 / (end_time - start_time)
        
        # Draw FPS on the screen
        cv2.putText(processed_frame, f"AI FPS: {inference_fps:.1f}", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display the result
        cv2.imshow("UvA Safe Crosswalk - Performance Test", processed_frame)
        
        # Press 'q' to stop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_on_video("video1.mp4")