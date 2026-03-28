import sys
import cv2

sys.path.insert(0, 'backend')

from detector import detect_signs
from ocr_engine import extract_text
from spatial import get_spatial_cue
from dedup import should_speak
from tts_engine import speak
from context_engine import build_speech

def main():
    print("VisionAid running. Point camera at a sign. Press Q to quit.")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
        
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break
            
        cv2.imshow('VisionAid', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
        frame_count += 1
        
        if frame_count % 3 != 0:
            continue
            
        # Encode the frame to JPEG bytes as expected by our detection logic
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not success:
            continue
            
        frame_bytes = buffer.tobytes()
        
        # Pipeline
        detections = detect_signs(frame_bytes)
        if not detections:
            continue
            
        best = max(detections, key=lambda d: d['confidence'])
        
        text, lang, ocr_conf = extract_text(best['cropped'])
        if not text or ocr_conf < 0.75:
            continue
            
        spatial = get_spatial_cue(best['bbox'], best['frame_size'])
        speech, is_danger = build_speech(text, spatial)
        
        if should_speak(text):
            print(f"[{lang}] [{ocr_conf:.0%}] {speech}")
            speak(speech, danger=is_danger)
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
