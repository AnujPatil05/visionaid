import sys

modules = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("cv2", "opencv-python"),
    ("ultralytics", "ultralytics"),
    ("paddleocr", "paddleocr"),
    ("paddle", "paddlepaddle"),
    ("pyttsx3", "pyttsx3"),
    ("numpy", "numpy"),
    ("PIL", "pillow"),
    ("multipart", "python-multipart")
]

def main():
    print("Verifying installations...")
    all_ok = True
    for import_name, pip_name in modules:
        try:
            __import__(import_name)
            print(f"[*] {pip_name}: OK")
        except ImportError as e:
            print(f"[ ] {pip_name}: ERROR - {e}")
            all_ok = False
            
    if all_ok:
        print("\nAll modules installed successfully!")
    else:
        print("\nSome modules failed to import.")
        sys.exit(1)

if __name__ == "__main__":
    main()
