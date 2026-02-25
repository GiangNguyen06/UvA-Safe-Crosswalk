import cv2
import zmq
import base64
import numpy as np
import os
from dotenv import load_dotenv
from detector import CrosswalkDetector
import os
from dotenv import load_dotenv


env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

load_dotenv(dotenv_path=env_path)

def receive_stream():
    pi_ip = os.getenv("PI_IP_HOME")
    port = os.getenv("ZMQ_PORT")
    
    if not pi_ip or not port:
        print("[ERROR] Could not find PI_IP or ZMQ_PORT in .env file!")
        return

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    
    socket.connect(f"tcp://{pi_ip}:{port}")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    detector = CrosswalkDetector()
    
    print(f"[INFO] AI System Ready. Connected to Pi at {pi_ip}")

    try:
        while True:
            jpg_as_text = socket.recv()
            jpg_original = base64.b64decode(jpg_as_text)
            jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
            frame = cv2.imdecode(jpg_as_np, flags=1)
            
            if frame is not None:
                processed_frame = detector.process_frame(frame)
                cv2.imshow("UvA Safe Crosswalk - AI Feed", processed_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as e:
        print(f"[ERROR] Stream interrupted: {e}")
    finally:
        cv2.destroyAllWindows()
        socket.close()
        context.term()

if __name__ == "__main__":
    receive_stream()