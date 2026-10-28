from ultralytics import YOLO
import torch  
import cv2

class CrosswalkDetector:
    def __init__(self):
        self.model = YOLO('yolo11n.pt') 
        
        if torch.cuda.is_available():
            self.model.to('cuda')
        
        # 0: person, 1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck
        self.target_classes = [0, 1, 2, 3, 5, 7]

    def process_frame(self, frame):
        results = self.model(
            frame, 
            verbose=False, 
            conf=0.5, 
            classes=self.target_classes 
        )
        
        annotated_frame = results[0].plot()
        
        detections = results[0].boxes.cls.tolist()
        
        if detections:
            class_names = [results[0].names[int(cls)] for cls in detections]
            print(f"Alert! Detected traffic: {class_names}")
            
        return annotated_frame
    

    def process_frame(self, frame):
        results = self.model(
            frame, 
            verbose=False, 
            conf=0.5, 
            classes=self.target_classes
        )
       
        annotated_frame = results[0].plot(
            boxes=False, 
            masks=True, 
            labels=True, 
            conf=True
        )
        
        if annotated_frame is None:
            return frame
            
        return annotated_frame



# class CrosswalkDetector:
#     def __init__(self):
#         # Load the model
#         self.model = YOLO('yolo11n.pt') 
        
#         if torch.cuda.is_available():
#             self.model.to('cuda')
#            
        
#         # 0: person, 1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck
#         self.target_classes = [0, 1, 2, 3, 5, 7]
        
#        
#         self.roi_y1, self.roi_y2 = 116, 707
#         self.roi_x1, self.roi_x2 = 1, 648
        
#        
#         self.danger_threshold = 150 

#     def process_frame(self, frame): 
#         incoming_lane_roi = frame[self.roi_y1:self.roi_y2, self.roi_x1:self.roi_x2]
        
#         results = self.model(
#             incoming_lane_roi, 
#             verbose=False, 
#             conf=0.5, 
#             classes=self.target_classes 
#         )
         
#         annotated_frame = results[0].plot()
        
#       
#         largest_box_width = 0
#         detections = results[0].boxes
             
#         if len(detections) > 0:
#             for box in detections:
#                 coords = box.xyxy[0].cpu().numpy()
#                 width = coords[2] - coords[0] # Calculate width
                                
#                 if width > largest_box_width:
#                     largest_box_width = width
                              
#             if largest_box_width >= self.danger_threshold:
#                 status = "DANGER"
#             else:
#                 status = "APPROACHING"
                
#         else:
#             status = "SAFE"
            
#         return annotated_frame, status, int(largest_box_width)

