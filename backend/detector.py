import cv2
import numpy as np
from ultralytics import YOLO

_model = None

def get_model():
    global _model
    if _model is None:
        _model = YOLO('yolo11n.pt')
    return _model

def sharpness_score(img):
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def detect_signs(frame_bytes: bytes, conf_threshold=0.40) -> list[dict]:
    np_arr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if frame is None:
        return []
        
    model = get_model()
    h, w = frame.shape[:2]
    
    results = model(frame, conf=conf_threshold, verbose=False)[0]
    
    detections = []
    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        conf = float(box.conf[0])
        label_idx = int(box.cls[0])
        label = model.names[label_idx] if hasattr(model, 'names') else str(label_idx)
        
        # Crop sign region with 10px padding (clamp to frame bounds)
        pad = 10
        crop_x1 = max(0, x1 - pad)
        crop_y1 = max(0, y1 - pad)
        crop_x2 = min(w, x2 + pad)
        crop_y2 = min(h, y2 + pad)
        
        cropped = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        
        detections.append({
            'bbox': (x1, y1, x2, y2),
            'frame_size': (w, h),
            'confidence': conf,
            'label': label,
            'cropped': cropped
        })
        
    if not detections:
        # Fallback: If YOLO misses a completely textual sign (like our printed demo signs),
        # treat the entire frame as the bounding box so PaddleOCR still scans the text!
        detections.append({
            'bbox': (0, 0, w, h),
            'frame_size': (w, h),
            'confidence': 0.99,
            'label': 'full_scan_fallback',
            'cropped': frame
        })
        
    return detections
