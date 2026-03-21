import cv2
import zmq
import base64
import numpy as np
import datetime

# --- CONFIGURATION ---
PI_IP = "100.119.133.35" # Your Pi Tailscale IP

# 1. Connect to the existing ZMQ stream
context = zmq.Context()
footage_socket = context.socket(zmq.SUB)
footage_socket.connect(f"tcp://{PI_IP}:5555")
footage_socket.setsockopt_string(zmq.SUBSCRIBE, "")

print("[*] Raw Recorder Connected. Waiting for video feed...")

# Grab the first frame to get the video dimensions
frame_data = footage_socket.recv()
img_array = np.frombuffer(base64.b64decode(frame_data), dtype=np.uint8)
first_frame = cv2.imdecode(img_array, 1)

# 2. Setup the Video Writer
height, width = first_frame.shape[:2]
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"raw_street_footage_{timestamp}.mp4"
out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'mp4v'), 15.0, (width, height))

print(f"[*] Recording clean, raw footage to: {filename}")
print("[*] Click on the video window and press 'q' to stop and save.")

# 3. The Recording Loop
while True:
    try:
        # Non-blocking receive
        frame_data = footage_socket.recv(flags=zmq.NOBLOCK)
        img_array = np.frombuffer(base64.b64decode(frame_data), dtype=np.uint8)
        frame = cv2.imdecode(img_array, 1)
        
        # Write to file
        out.write(frame)
        
        # Show a tiny preview window just so you know it's working
        cv2.imshow("Raw Recorder (Recording...)", cv2.resize(frame, (320, 240)))
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    except zmq.Again:
        continue # No new frame, keep looping

# Clean up and save the file
out.release()
cv2.destroyAllWindows()
print("[*] Raw video saved successfully.")