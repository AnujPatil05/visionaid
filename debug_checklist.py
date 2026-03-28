import sys
import os
import cv2
import numpy as np
import time
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

GREEN = '\033[92m'
RED = '\033[91m'
NC = '\033[0m'

def run_step(name, func, fix_suggestion):
    try:
        print(f"Running Step: {name}...")
        func()
        print(f"{GREEN}PASS: {name}{NC}\n")
    except Exception as e:
        print(f"{RED}FAIL: {name}{NC}")
        print(f"{RED}Error: {e}{NC}")
        print(f"\nFIX SUGGESTION: {fix_suggestion}")
        sys.exit(1)

def step1_yolo():
    from detector import get_model
    get_model()

def step2_ocr():
    from ocr_engine import extract_text
    img = np.full((100, 300, 3), 255, dtype=np.uint8)
    cv2.putText(img, "EXIT", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
    text, lang, conf = extract_text(img)
    assert "exit" in text.lower(), f"Expected 'exit', got '{text}'"

def step3_tts():
    from tts_engine import speak
    speak("VisionAid is working")
    time.sleep(3)
    ans = input("Did you hear it? [y/n]: ").strip().lower()
    assert ans == 'y', "User did not hear TTS audio."

def step4_health():
    res = requests.get("http://localhost:8000/health", timeout=3)
    assert res.status_code == 200, f"Status code {res.status_code}"

def step5_process():
    # Construct a valid payload and push it up to 3 times to un-skip the logic buffer
    img = np.full((200, 400, 3), 255, dtype=np.uint8)
    cv2.putText(img, "EXIT", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
    success, buffer = cv2.imencode('.jpg', img)
    if not success:
        raise ValueError("Failed to encode image")
        
    for _ in range(3):
        res = requests.post(
            "http://localhost:8000/process", 
            files={'file': ('test.jpg', buffer.tobytes(), 'image/jpeg')},
            timeout=5
        )
        data = res.json()
        if data.get("action") not in ["skip", "buffering"]:    
            print(f"Response: {data}")        
            return
            
    raise RuntimeError("Server never broke out of its buffering threshold.")

def main():
    run_step("1. YOLO", step1_yolo, "Check if 'yolo11n.pt' is found by ultralytics.")
    run_step("2. OCR", step2_ocr, "Check if PaddleOCR and paddlepaddle are installed securely.")
    run_step("3. TTS", step3_tts, "Check your default system audio output and test pyttsx3 permissions.")
    run_step("4. Server Health", step4_health, "Start the FastAPI server via 'python backend/main.py' in a separate terminal.")
    run_step("5. POST /process", step5_process, "Check server console. Frame skips/buffering might have caught the mocked text image.")
    
    print(f"{GREEN}ALL DIAGNOSTICS PASSED.{NC}")

if __name__ == "__main__":
    main()
