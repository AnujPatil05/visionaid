import sys
import os
import socket
import subprocess
import time
import requests

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    if sys.prefix == sys.base_prefix:
        print("WARNING: Not running inside a virtual environment.")
        
    try:
        import ultralytics
        from paddleocr import PaddleOCR
    except ImportError as e:
        print(f"Error importing models: {e}")
        print("Please install requirements.")
        sys.exit(1)
        
    ip = get_local_ip()
    print(f"\nUpdate api_service.dart baseUrl to: http://{ip}:8000\n")
    
    print("Starting FastAPI server...")
    proc = subprocess.Popen([sys.executable, 'backend/main.py'])
    
    health_url = "http://localhost:8000/health"
    passed = False
    time.sleep(2)
    for _ in range(5):
        try:
            res = requests.get(health_url, timeout=2)
            if res.status_code == 200:
                passed = True
                break
        except Exception:
            time.sleep(1)
            
    if passed:
        print("\nVisionAid server running. Open the Flutter app now.\n")
    else:
        print("\nFailed to start VisionAid server.")
        proc.terminate()
        sys.exit(1)
        
    print("--- DEMO CHECKLIST ---")
    print(" [ ] Phone and laptop on same WiFi")
    print(" [ ] flutter run on phone")
    print(" [ ] Volume at max on phone")
    print(" [ ] A4 signs printed and ready")
    print(" [ ] TalkBack tested")
    print(" [ ] Fallback video ready")
    print("----------------------")
    print(f"API also available at http://{ip}:8000/qrcode to scan.\n")
    print("Press Ctrl+C to stop the server.")
    
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nStopping server...")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
