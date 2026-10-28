import cv2
import zmq
import base64
import time
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

def start_stream():
    port = os.getenv("ZMQ_PORT", "5555")
    
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    
    socket.bind(f"tcp://*:{port}") 
    print(f"[INFO] ZeroMQ Server started. Broadcasting on port {port}...")

    # Hardware Pipeline: MUST be 30/1. max-buffers=1 drop=true kills the queue.
    pipeline = "v4l2src device=/dev/video0 ! image/jpeg,width=640,height=480,framerate=30/1 ! jpegdec ! videoconvert ! appsink max-buffers=1 drop=true"
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    
    time.sleep(2)
    print("[INFO] Camera warmed up. Streaming video...")

    frame_counter = 0

    try:
        while True:
            # Always grab the frame to keep the hardware buffer empty
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to grab frame.")
                time.sleep(0.5)
                continue
            
            # 2. Software Frame Dropper: Skip encoding every other frame
            frame_counter += 1
            if frame_counter % 2 == 0:
                continue # Instantly loops back to grab the next frame
            
            # 3. Compress and encode (Quality at 60 for speed)
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            jpg_as_text = base64.b64encode(buffer)
            socket.send(jpg_as_text)

    except KeyboardInterrupt:
        print("\n[INFO] Stopping stream...")
        
    finally:
        cap.release()
        socket.close()
        context.term()
        print("[INFO] Hardware released safely.")

if __name__ == "__main__":
    start_stream()