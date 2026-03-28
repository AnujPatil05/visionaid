import cv2
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from detector import detect_signs
from ocr_engine import extract_text
from context_engine import build_speech
from spatial import get_spatial_cue

def record():
    os.makedirs("demo_assets", exist_ok=True)
    out_path = "demo_assets/fallback_demo.mp4"
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, 30.0, (1280, 720))
    
    print("Recording... Press Q to stop.")
    
    frame_count = 0
    start_time = time.time()
    last_speech = ""
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        display_frame = frame.copy()
        
        # Test inference using the same 3-frame polling pattern to show active response mapping
        if frame_count % 3 == 0:
            success, enc_buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if success:
                frame_bytes = enc_buffer.tobytes()
                detections = detect_signs(frame_bytes)
                if detections:
                    best = max(detections, key=lambda d: d['confidence'])
                    text, lang, ocr_conf = extract_text(best['cropped'])
                    if text and ocr_conf >= 0.75:
                        spatial = get_spatial_cue(best['bbox'], best['frame_size'])
                        speech, _ = build_speech(text, spatial)
                        last_speech = speech

        if last_speech:
            cv2.putText(display_frame, last_speech, (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
        final_frame = cv2.resize(display_frame, (1280, 720))
        out.write(final_frame)
        cv2.imshow("Recording", final_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    duration = time.time() - start_time
    print(f"Demo recorded. Duration: {duration:.1f}s. File: {out_path}")

if __name__ == "__main__":
    record()
