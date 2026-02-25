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
    

    '''def process_frame(self, frame):
        results = self.model(
            frame, 
            verbose=False, 
            conf=0.5, 
            classes=self.target_classes
        )
        
        # We use 'masks=True' to show the colored shapes.
        # 'boxes=False' to hide the rectangles.
        # Note: If 'alpha' fails, the default transparency is usually fine.
        annotated_frame = results[0].plot(
            boxes=False, 
            masks=True, 
            labels=True, 
            conf=True
        )
        
        # Safety check: if no objects are detected, plot() might return None or 
        # a blank result in rare edge cases. Let's ensure we return the frame.
        if annotated_frame is None:
            return frame
            
        return annotated_frame'''
    
