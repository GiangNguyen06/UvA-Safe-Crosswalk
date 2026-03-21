##### TRAPEZOID ZONE CALIBRATION + YOLOv11n VEHICLE DETECTION #####
import cv2
import numpy as np
import torch
from ultralytics import YOLO
import socket

# --- CONFIGURATION ---
VIDEO_PATH = "videos/video4.mp4" 

# UDP Setup 
PI_IP = "100.119.133.35" 
PI_PORT = 9000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Zone Storage - ORDERED FROM FURTHEST TO CLOSEST
zones = {
    "YELLOW": {
        "points": [], 
        "color": (0, 255, 255),     # Match: 0xFFFFFF00 (Pure Bright Yellow)
        "message": "> 30M AWAY"
    },
    "ORANGE": {
        "points": [], 
        "color": (0, 152, 255),     # Match: 0xFFFF9800 (Orange)
        "message": "15-30M AWAY"
    },
    "RED": {
        "points": [], 
        "color": (54, 67, 244),      # Match: 0xFFF44336 (Red)
        "message": "< 15M AWAY"
    }
}
current_drawing_zone = "RED" # Start by drawing the furthest zone
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

    # UI Instructions
    if not calibration_done:
        instruction = f"Draw {current_drawing_zone} ZONE (Click 4 points)"
    else:
        instruction = "Done! Press 'ENTER' to start AI!"
        
    cv2.putText(frame_display, instruction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imshow("Calibrate Zones (Full Frame)", frame_display)

# Load Video & Start Calibration
cap = cv2.VideoCapture(VIDEO_PATH)
ret, first_frame = cap.read()
if not ret:
    print("Failed to load video!")
    exit()

# Setup frame for calibration
calibration_frame = first_frame.copy()

cv2.imshow("Calibrate Zones (Full Frame)", calibration_frame)
cv2.setMouseCallback("Calibrate Zones (Full Frame)", click_event, {'frame': calibration_frame})

print("--- CALIBRATION MODE ---")
print("Click 4 times to draw the YELLOW zone (Furthest).")
print("Then 4 times for ORANGE (Middle), then 4 for RED (Closest).")
print("Press ENTER in the window when finished.")

while True:
    if cv2.waitKey(1) == 13 and calibration_done: 
        break
cv2.destroyWindow("Calibrate Zones (Full Frame)")

for z in zones:
    zones[z]["points"] = np.array(zones[z]["points"], np.int32)

# --- 2. AI DETECTION LOOP ---
print("\n--- STARTING AI ---")
model = YOLO('yolo11n.pt')
if torch.cuda.is_available(): model.to('cuda')
target_classes = [2, 3, 5, 7] # Cars, Motorcycles, Buses, Trucks

while True:
    ret, frame = cap.read()
    if not ret: break
    
    # Run YOLO on the full frame
    results = model(frame, verbose=False, conf=0.4, classes=target_classes)
    
    # Draw zones on the frame 
    overlay = frame.copy()
    for z in zones.values():
        cv2.fillPoly(overlay, [z["points"]], z["color"])
    frame = cv2.addWeighted(overlay, 0.2, frame, 0.8, 0) # 20% opacity

    closest_status = "STOPPED OR GONE"
    status_color = (80, 175, 76)  # Green when clear (Match: 0xFF4CAF50)
    
    if len(results[0].boxes) > 0:
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            
            # Bottom center of the car 
            car_bottom_x = int((x1 + x2) / 2)
            car_bottom_y = y2
            
            cv2.circle(frame, (car_bottom_x, car_bottom_y), 5, (255, 255, 255), -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)

            # Check which zone the car is inside (Priority: Red -> Orange -> Yellow)
            if cv2.pointPolygonTest(zones["RED"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                closest_status = zones["RED"]["message"]
                status_color = zones["RED"]["color"]
            elif closest_status != zones["RED"]["message"] and cv2.pointPolygonTest(zones["ORANGE"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                closest_status = zones["ORANGE"]["message"]
                status_color = zones["ORANGE"]["color"]
            elif closest_status not in [zones["RED"]["message"], zones["ORANGE"]["message"]] and cv2.pointPolygonTest(zones["YELLOW"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                closest_status = zones["YELLOW"]["message"]
                status_color = zones["YELLOW"]["color"]
                
    # Send UDP to Pi
    try:
        sock.sendto(closest_status.encode(), (PI_IP, PI_PORT))
    except Exception as e:
        print(f"Network error: {e}")
    
    # Draw Status Text (Black outline, then colored fill)
    cv2.putText(frame, f"STATUS: {closest_status}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
    cv2.putText(frame, f"STATUS: {closest_status}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
    
    cv2.imshow("SafeStride AI (Full Frame)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break

cap.release()
cv2.destroyAllWindows()