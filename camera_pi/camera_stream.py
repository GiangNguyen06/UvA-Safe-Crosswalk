import cv2
import zmq
import base64
import time
import os
from dotenv import load_dotenv, find_dotenv

# Load hidden variables (finds .env in the root folder)
load_dotenv(find_dotenv())

def start_stream():
    # Use the port from .env, default to 5555 if not found
    port = os.getenv("ZMQ_PORT", "5555")
    
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    
    # We still use * because the Pi needs to bind to its own local interfaces
    socket.bind(f"tcp://*:{port}") 
    print(f"[INFO] ZeroMQ Server started. Broadcasting on port {port}...")

    cap = cv2.VideoCapture(0)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    time.sleep(2)
    
    print("[INFO] Camera warmed up. Streaming video...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to grab frame.")
                time.sleep(1)
                continue
            
            # Compress and encode
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
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