import os
import sys
import numpy as np
from PIL import Image, ImageDraw

def main():
    print("Starting model downloads for VisionAid...\n")
    try:
        from ultralytics import YOLO
    except ImportError:
        print("ERROR: ultralytics is not installed. Run pip install ultralytics.")
        sys.exit(1)
        
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        print("ERROR: paddleocr is not installed. Run pip install paddleocr.")
        sys.exit(1)

    print("1. Downloading YOLOv11 nano model...")
    try:
        yolo_model = YOLO('yolo11n.pt')
        print("   YOLOv11 nano downloaded/loaded.\n")
    except Exception as e:
        print(f"   [ERROR] Failed to download YOLO: {e}\n")
        yolo_model = None

    print("2. Downloading PaddleOCR English model...")
    try:
        ocr_en = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        print("   PaddleOCR English downloaded/loaded.\n")
    except Exception as e:
        print(f"   [ERROR] Failed to download PaddleOCR EN: {e}\n")
        ocr_en = None

    print("3. Downloading PaddleOCR Hindi model...")
    try:
        ocr_hi = PaddleOCR(use_angle_cls=True, lang='hi', show_log=False)
        print("   PaddleOCR Hindi downloaded/loaded.\n")
    except Exception as e:
        print(f"   [ERROR] Failed to download PaddleOCR HI: {e}\n")
        ocr_hi = None

    print("--- Running Smoke Tests ---")
    all_passed = True
    
    if yolo_model:
        print("Testing YOLOv11...")
        try:
            black_img = np.zeros((480, 640, 3), dtype=np.uint8)
            results = yolo_model(black_img, verbose=False)
            print("   YOLOv11 smoke test passed.")
        except Exception as e:
            print(f"   [ERROR] YOLOv11 smoke test failed: {e}")
            all_passed = False
    else:
        all_passed = False

    if ocr_en:
        print("Testing PaddleOCR (English)...")
        try:
            img = Image.new('RGB', (200, 100), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            d.text((50, 40), "TEST", fill=(0, 0, 0))
            img_arr = np.array(img)
            result = ocr_en.ocr(img_arr, cls=True)
            print("   PaddleOCR smoke test passed.")
        except Exception as e:
            print(f"   [ERROR] PaddleOCR smoke test failed: {e}")
            all_passed = False
    else:
        all_passed = False

    print("\n===============================")
    if all_passed:
        print("All models ready")
    else:
        print("Finished with errors. Please check the logs above.")

if __name__ == "__main__":
    main()
