##### LAPTOP -> PI RELAY -> WATCH (BUFFERED TRACKING TEST) #####
import cv2
import numpy as np
import torch
from ultralytics import YOLO
import socket

# --- CONFIGURATION ---
VIDEO_PATH = "videos/video6.mp4" 

PI_IP = "100.119.133.35"  
PI_PORT = 9001            

# NEW: How many consecutive frames must the car be stopped before we trust it?
REQUIRED_STOP_FRAMES = 15 

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print(f"[*] Laptop AI shooting alerts to Pi Relay at {PI_IP}:{PI_PORT}...")

zones = {
    "RED": {"points": [], "color": (54, 67, 244), "message": "< 15M AWAY"},
    "ORANGE": {"points": [], "color": (0, 152, 255), "message": "15-30M AWAY"},
    "YELLOW": {"points": [], "color": (0, 255, 255), "message": "> 30M AWAY"}
}
current_drawing_zone = "RED" 
calibration_done = False

def click_event(event, x, y, flags, param):
    global current_drawing_zone, calibration_done
    frame_display = param['frame'].copy()
    
    if event == cv2.EVENT_LBUTTONDOWN and not calibration_done:
        if current_drawing_zone:
            zones[current_drawing_zone]["points"].append([x, y])
            if len(zones[current_drawing_zone]["points"]) == 4:
                if current_drawing_zone == "RED": current_drawing_zone = "ORANGE"
                elif current_drawing_zone == "ORANGE": current_drawing_zone = "YELLOW"
                elif current_drawing_zone == "YELLOW": 
                    current_drawing_zone = None
                    calibration_done = True
        
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
    cv2.imshow("Laptop AI Video Test", frame_display)

cap = cv2.VideoCapture(VIDEO_PATH)
ret, first_frame = cap.read()
if not ret:
    print("Failed to load video!")
    exit()

cv2.imshow("Laptop AI Video Test", first_frame.copy())
cv2.setMouseCallback("Laptop AI Video Test", click_event, {'frame': first_frame.copy()})

while True:
    if cv2.waitKey(1) == 13 and calibration_done: 
        break
cv2.destroyWindow("Laptop AI Video Test")

for z in zones:
    zones[z]["points"] = np.array(zones[z]["points"], np.int32)

# --- AI DETECTION & TRACKING LOOP ---
model = YOLO('yolo11n.pt')
if torch.cuda.is_available(): model.to('cuda')
target_classes = [2, 3, 5, 7] 

# Memory dictionaries
car_history = {}
stopped_counter = {} # NEW: Tracks how long a car has been stopped

while True:
    ret, frame = cap.read()
    if not ret: 
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        car_history.clear() 
        stopped_counter.clear() # Clear memory when video loops!
        continue
    
    results = model.track(frame, persist=True, verbose=False, conf=0.4, classes=target_classes)
    
    overlay = frame.copy()
    for z in zones.values():
        cv2.fillPoly(overlay, [z["points"]], z["color"])
    frame = cv2.addWeighted(overlay, 0.2, frame, 0.8, 0) 

    global_status = "STOPPED OR GONE"
    status_color = (80, 175, 76)  
    hierarchy = {"STOPPED OR GONE": 0, "SAFE TO CROSS": 1, "> 30M AWAY": 2, "15-30M AWAY": 3, "< 15M AWAY": 4}
    
    current_frame_areas = {}

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.int().cpu().tolist()

        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = map(int, box)
            car_bottom_x = int((x1 + x2) / 2)
            car_bottom_y = y2
            
            area = (x2 - x1) * (y2 - y1)
            current_frame_areas[track_id] = area
            
            cv2.circle(frame, (car_bottom_x, car_bottom_y), 5, (255, 255, 255), -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)

            car_status = "STOPPED OR GONE"

            # Check Zones
            if cv2.pointPolygonTest(zones["RED"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                if track_id in car_history:
                    # Is it growing? (Moving towards you)
                    if area > car_history[track_id] * 1.02:
                        car_status = zones["RED"]["message"] 
                        stopped_counter[track_id] = 0 # Reset trust counter to zero!
                    else:
                        # Car stopped growing. Start the trust counter.
                        stopped_counter[track_id] = stopped_counter.get(track_id, 0) + 1
                        
                        # Has it been stopped long enough to trust?
                        if stopped_counter[track_id] >= REQUIRED_STOP_FRAMES:
                            car_status = "STOPPED OR GONE" # We trust it now!
                        else:
                            car_status = zones["RED"]["message"] # Keep alarming just in case!
                else:
                    car_status = zones["RED"]["message"] 
                    stopped_counter[track_id] = 0

            elif cv2.pointPolygonTest(zones["ORANGE"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                car_status = zones["ORANGE"]["message"]
            elif cv2.pointPolygonTest(zones["YELLOW"]["points"], (car_bottom_x, car_bottom_y), False) >= 0:
                car_status = zones["YELLOW"]["message"]
            
            if hierarchy[car_status] > hierarchy.get(global_status, 0):
                global_status = car_status
                if global_status == "< 15M AWAY": status_color = zones["RED"]["color"]
                elif global_status == "15-30M AWAY": status_color = zones["ORANGE"]["color"]
                elif global_status == "> 30M AWAY": status_color = zones["YELLOW"]["color"]

    car_history = current_frame_areas.copy()
                
    try:
        sock.sendto(global_status.encode(), (PI_IP, PI_PORT))
    except Exception as e:
        print(f"Network error: {e}")
    
    display_text = "SAFE TO CROSS" if global_status == "STOPPED OR GONE" else global_status
    cv2.putText(frame, f"STATUS: {display_text}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 4)
    cv2.putText(frame, f"STATUS: {display_text}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
    
    cv2.imshow("Laptop AI Video Test", frame)
    if cv2.waitKey(30) & 0xFF == ord('q'): 
        break

cap.release()
cv2.destroyAllWindows()