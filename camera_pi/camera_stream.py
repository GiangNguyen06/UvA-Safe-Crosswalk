import cv2
import zmq
import base64
import time

def start_stream():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555") 
    print("[INFO] ZeroMQ Server started. Broadcasting on port 5555...")

    cap = cv2.VideoCapture(0)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    time.sleep(2)
    
    print("[INFO] Camera warmed up. Streaming video...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to grab frame. Is the USB camera plugged in?")
                time.sleep(1)
                continue
            
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