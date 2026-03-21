import cv2
import numpy as np
import torch
from ultralytics import YOLO
import socket
import zmq
import base64

# --- CONFIGURATION ---
PI_IP = "100.119.133.35" # The Pi's Tailscale IP

# Custom crop dimensions (Match your specific camera angle)
ROI_Y1, ROI_Y2 = 116, 707
ROI_X1, ROI_X2 = 1, 648

# 1. ZMQ Setup (Receiving Video from Pi on Port 5555)
context = zmq.Context()
footage_socket = context.socket(zmq.SUB)
footage_socket.connect(f"tcp://{PI_IP}:5555")
footage_socket.setsockopt_string(zmq.SUBSCRIBE, "") # Subscribe to all messages
print(f"[*] Connected to Pi video stream at {PI_IP}:5555")

# 2. UDP Setup (Sending Alerts back to Pi on Port 9001)
PI_PORT_UDP = 9001
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- ZONE CALIBRATION STATE ---
zones = {
    "RED": {"points": [], "color": (0, 0, 255), "message": "< 15M AWAY"},
    "YELLOW": {"points": [], "color": (0, 255, 255), "message": "15-30M AWAY"},
    "GREEN": {"points": [], "color": (0, 255, 0), "message": "> 30M AWAY"}
}
current_drawing_zone = "RED"
calibration_done = False

def click_event(event, x, y, flags, param):
    global current_drawing_zone, calibration_done
    frame_display = param['cropped_frame'].copy()
    
    if event == cv2.EVENT_LBUTTONDOWN and not calibration_done:
        if current_drawing_zone:
            zones[current_drawing_zone]["points"].append([x, y])
            
            # Switch zones if 4 points are collected
            if len(zones[current_drawing_zone]["points"]) == 4:
                if current_drawing_zone == "RED": current_drawing_zone = "YELLOW"
                elif current_drawing_zone == "YELLOW": current_drawing_zone = "GREEN"
                elif current_drawing_zone == "GREEN": 
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

    # UI Instructions
    if not calibration_done:
        instruction = f"Draw {current_drawing_zone} ZONE (Click 4 points)"
    else:
        instruction = "Done! Press 'ENTER' to start AI!"
        
    cv2.putText(frame_display, instruction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imshow("Calibrate Zones (Cropped)", frame_display)

# --- GRAB FIRST FRAME FOR CALIBRATION ---
print("[*] Waiting for the first frame from the Pi...")
# Wait until we receive the first ZMQ frame to draw the zones
frame_data = footage_socket.recv() 
img_b64decode = base64.b64decode(frame_data)
img_array = np.frombuffer(img_b64decode, dtype=np.uint8)
first_frame = cv2.imdecode(img_array, 1)

# Apply the crop BEFORE calibration
cropped_first_frame = first_frame[ROI_Y1:ROI_Y2, ROI_X1:ROI_X2].copy()

cv2.imshow("Calibrate Zones (Cropped)", cropped_first_frame)
cv2.setMouseCallback("Calibrate Zones (Cropped)", click_event, {'cropped_frame': cropped_first_frame})

print("--- CALIBRATION MODE ---")
print("Click 4 times to draw the RED zone.")
print("Then 4 times for YELLOW, then 4 for GREEN.")
print("Press ENTER in the window when finished drawing zones.")

while True:
    if cv2.waitKey(1) == 13 and calibration_done: 
        break
cv2.destroyWindow("Calibrate Zones (Cropped)")

# Convert points to numpy arrays for OpenCV processing
for z in zones:
    zones[z]["points"] = np.array(zones[z]["points"], np.int32)

# AI DETECTION LOOP 
print("\n--- STARTING AI ---") 
model = YOLO('yolo11n.pt')
if torch.cuda.is_available(): model.to('cuda')
target_classes = [2, 3, 5, 7] # Cars, Motorcycles, Buses, Trucks

while True:
    # --- GET FRAME FROM ZMQ ---
    try:
        frame_data = footage_socket.recv(flags=zmq.NOBLOCK) # Non-blocking so it doesn't freeze
        img_b64decode = base64.b64decode(frame_data)
        img_array = np.frombuffer(img_b64decode, dtype=np.uint8)
        frame = cv2.imdecode(img_array, 1)
    except zmq.Again:
        # No new frame arrived yet, just keep looping
        continue

    # ALWAYS crop the frame first!
    crop = frame[ROI_Y1:ROI_Y2, ROI_X1:ROI_X2]
    
    # Run YOLO only on the cropped area
    results = model(crop, verbose=False, conf=0.4, classes=target_classes)
    
    # Draw zones on the crop (Semi-transparent overlay)
    overlay = crop.copy()
    for z in zones.values():
        cv2.fillPoly(overlay, [z["points"]], z["color"])
    crop = cv2.addWeighted(overlay, 0.2, crop, 0.8, 0) # 20% opacity

    closest_status = "STOPPED OR GONE"
    
    if len(results[0].boxes) > 0:
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            
            # Bottom center of the car (where the tires touch the road)
            car_bottom_x = int((x1 + x2) / 2)
            car_bottom_y = y2
            
            cv2.circle(crop, (car_bottom_x, car_bottom_y), 5, (255, 255, 255), -1)
            cv2.rectangle(crop, (x1, y1), (x2, y2), (255, 0, 255), 2)

            # Check which zone the car is inside (Priority: Red -> Yellow -> Green)
            if cv2.pointPolygonTest(zones["RED"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                closest_status = zones["RED"]["message"]
            elif closest_status != zones["RED"]["message"] and cv2.pointPolygonTest(zones["YELLOW"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                closest_status = zones["YELLOW"]["message"]
            elif closest_status not in [zones["RED"]["message"], zones["YELLOW"]["message"]] and cv2.pointPolygonTest(zones["GREEN"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                closest_status = zones["GREEN"]["message"]

    # --- SEND THE DATA TO PI ---
    try:
        sock.sendto(closest_status.encode(), (PI_IP, PI_PORT_UDP))
    except Exception as e:
        print(f"Network error: {e}")
    
    # Display the result
    cv2.putText(crop, f"STATUS: {closest_status}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)
    cv2.putText(crop, f"STATUS: {closest_status}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    cv2.imshow("SafeStride AI (Cropped)", crop)
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break

cv2.destroyAllWindows()