import cv2
import numpy as np
import torch
from ultralytics import YOLO
import socket
import zmq
import base64
import datetime # ADDED: For timestamping our video files

# --- CONFIGURATION ---
PI_IP = "100.119.133.35" # The Pi's Tailscale IP

# 1. ZMQ Setup (Receiving Video from Pi on Port 5555)
context = zmq.Context()
footage_socket = context.socket(zmq.SUB)
footage_socket.connect(f"tcp://{PI_IP}:5555")
footage_socket.setsockopt_string(zmq.SUBSCRIBE, "") 
print(f"[*] Connected to Pi video stream at {PI_IP}:5555")

# 2. UDP Setup (Sending Alerts back to Pi on Port 9001)
PI_PORT_UDP = 9001
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Zone Storage - ORDERED FROM FURTHEST TO CLOSEST
zones = {
    "YELLOW": {
        "points": [], 
        "color": (0, 255, 255),     
        "message": "> 30M AWAY"
    },
    "ORANGE": {
        "points": [], 
        "color": (0, 152, 255),     
        "message": "15-30M AWAY"
    },
    "RED": {
        "points": [], 
        "color": (54, 67, 244),      
        "message": "< 15M AWAY"
    }
}
current_drawing_zone = "RED" 
calibration_done = False

def click_event(event, x, y, flags, param):
    global current_drawing_zone, calibration_done
    frame_display = param['frame'].copy()
    
    if event == cv2.EVENT_LBUTTONDOWN and not calibration_done:
        if current_drawing_zone:
            zones[current_drawing_zone]["points"].append([x, y])
            
            # Switch zones if 4 points are collected
            if len(zones[current_drawing_zone]["points"]) == 4:
                if current_drawing_zone == "RED": current_drawing_zone = "ORANGE"
                elif current_drawing_zone == "ORANGE": current_drawing_zone = "YELLOW"
                elif current_drawing_zone == "YELLOW": 
                    current_drawing_zone = None
                    calibration_done = True
        
    # Draw all completed and in-progress zones
    for zone_name, zone_data in zones.items():
        pts = zone_data["points"]
        if len(pts) > 0:
            for p in pts:
                cv2.circle(frame_display, tuple(p), 5, zone_data["color"], -1)
            if len(pts) > 1:
                cv2.polylines(frame_display, [np.array(pts)], isClosed=(len(pts)==4), color=zone_data["color"], thickness=2)

    if not calibration_done:
        instruction = f"Draw {current_drawing_zone} ZONE (Click 4 points)"
    else:
        instruction = "Done! Press 'ENTER' to start AI!"
        
    cv2.putText(frame_display, instruction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imshow("Calibrate Zones (Live Stream)", frame_display)

# --- GRAB FIRST FRAME FOR CALIBRATION ---
print("[*] Waiting for the first frame from the Pi...")
frame_data = footage_socket.recv() 
img_b64decode = base64.b64decode(frame_data)
img_array = np.frombuffer(img_b64decode, dtype=np.uint8)
first_frame = cv2.imdecode(img_array, 1)

cv2.imshow("Calibrate Zones (Live Stream)", first_frame)
cv2.setMouseCallback("Calibrate Zones (Live Stream)", click_event, {'frame': first_frame})

print("--- CALIBRATION MODE ---")
print("Click 4 times to draw the YELLOW zone (Furthest).")
print("Then 4 times for ORANGE (Middle), then 4 for RED (Closest).")
print("Press ENTER in the window when finished drawing zones.")

while True:
    if cv2.waitKey(1) == 13 and calibration_done: 
        break
cv2.destroyWindow("Calibrate Zones (Live Stream)")

for z in zones:
    zones[z]["points"] = np.array(zones[z]["points"], np.int32)

# --- VIDEO RECORDER SETUP ---
frame_height, frame_width = first_frame.shape[:2]
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
video_filename = f"safestride_demo_ai_{timestamp}.mp4"
# Using mp4v codec which is highly compatible for Windows/OpenCV
fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
# 15.0 is the FPS. It's a safe guess for a network stream.
out = cv2.VideoWriter(video_filename, fourcc, 15.0, (frame_width, frame_height))
print(f"[*] Recording live AI footage to: {video_filename}")

# --- AI DETECTION LOOP ---
print("\n--- STARTING AI ---") 
model = YOLO('yolo11n.pt')
if torch.cuda.is_available(): model.to('cuda')
target_classes = [2, 3, 5, 7] 

while True:
    try:
        frame_data = footage_socket.recv(flags=zmq.NOBLOCK) 
        img_b64decode = base64.b64decode(frame_data)
        img_array = np.frombuffer(img_b64decode, dtype=np.uint8)
        frame = cv2.imdecode(img_array, 1)
    except zmq.Again:
        continue
    
    results = model(frame, verbose=False, conf=0.4, classes=target_classes)
    
    overlay = frame.copy()
    for z in zones.values():
        cv2.fillPoly(overlay, [z["points"]], z["color"])
    frame = cv2.addWeighted(overlay, 0.2, frame, 0.8, 0) 

    closest_status = "STOPPED OR GONE"
    status_color = (80, 175, 76)  
    
    if len(results[0].boxes) > 0:
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            
            car_bottom_x = int((x1 + x2) / 2)
            car_bottom_y = y2
            
            cv2.circle(frame, (car_bottom_x, car_bottom_y), 5, (255, 255, 255), -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)

            if cv2.pointPolygonTest(zones["RED"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                closest_status = zones["RED"]["message"]
                status_color = zones["RED"]["color"]
            elif closest_status != zones["RED"]["message"] and cv2.pointPolygonTest(zones["ORANGE"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                closest_status = zones["ORANGE"]["message"]
                status_color = zones["ORANGE"]["color"]
            elif closest_status not in [zones["RED"]["message"], zones["ORANGE"]["message"]] and cv2.pointPolygonTest(zones["YELLOW"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                closest_status = zones["YELLOW"]["message"]
                status_color = zones["YELLOW"]["color"]

    try:
        sock.sendto(closest_status.encode(), (PI_IP, PI_PORT_UDP))
    except Exception as e:
        print(f"Network error: {e}")
    
    cv2.putText(frame, f"STATUS: {closest_status}", (10, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
    cv2.putText(frame, f"STATUS: {closest_status}", (10, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
    
    # --- WRITE FRAME TO VIDEO FILE ---
    out.write(frame)
    
    cv2.imshow("SafeStride AI (Live Stream)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break

# --- CLEANUP ---
out.release() # CRITICAL: This saves and closes the video file!
cv2.destroyAllWindows()