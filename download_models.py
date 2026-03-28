import os
import sys
import numpy as np
from PIL import Image, ImageDraw

# Resolve paths relative to THIS script, not the caller's CWD
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(SCRIPT_DIR, 'backend')
MODEL_PATH  = os.path.join(BACKEND_DIR, 'yolo11n.pt')


def main():
    print("Starting model downloads for VisionAid...\n")

    # ------------------------------------------------------------------ YOLO
    try:
        from ultralytics import YOLO
    except ImportError:
        print("ERROR: ultralytics is not installed. Run pip install ultralytics.")
        sys.exit(1)

    print("1. Downloading YOLOv11 nano model...")
    yolo_model = None
    try:
        # Download to backend/ so detector.py can always find it there
        yolo_model = YOLO('yolo11n.pt')
        # Export/save to backend dir if not already there
        if not os.path.exists(MODEL_PATH):
            import shutil
            # Ultralytics caches to ~/.config/Ultralytics/ — copy to backend/
            import ultralytics
            cache_dir = os.path.join(os.path.expanduser('~'), '.config', 'Ultralytics')
            cached = os.path.join(cache_dir, 'yolo11n.pt')
            if os.path.exists(cached):
                shutil.copy(cached, MODEL_PATH)
                print(f"   Copied to {MODEL_PATH}")
        print("   YOLOv11 nano ready.\n")
    except Exception as e:
        print(f"   [ERROR] Failed to download YOLO: {e}\n")

    # ---------------------------------------------------------------- EasyOCR
    try:
        import easyocr
    except ImportError:
        print("ERROR: easyocr is not installed. Run: pip install easyocr")
        sys.exit(1)

    print("2. Downloading EasyOCR English model...")
    ocr_reader = None
    try:
        ocr_reader = easyocr.Reader(['en'], gpu=False)
        print("   EasyOCR English downloaded/loaded.\n")
    except Exception as e:
        print(f"   [ERROR] Failed to initialise EasyOCR EN: {e}\n")

    print("3. Downloading EasyOCR Hindi model...")
    try:
        easyocr.Reader(['en', 'hi'], gpu=False)
        print("   EasyOCR Hindi downloaded/loaded.\n")
    except Exception as e:
        print(f"   [ERROR] Failed to initialise EasyOCR HI: {e}\n")

    # ----------------------------------------------------------- Smoke tests
    print("--- Running Smoke Tests ---")
    all_passed = True

    if yolo_model:
        print("Testing YOLOv11...")
        try:
            black_img = np.zeros((480, 640, 3), dtype=np.uint8)
            yolo_model(black_img, verbose=False)
            print("   YOLOv11 smoke test passed.")
        except Exception as e:
            print(f"   [ERROR] YOLOv11 smoke test failed: {e}")
            all_passed = False
    else:
        all_passed = False

    if ocr_reader:
        print("Testing EasyOCR...")
        try:
            img = Image.new('RGB', (200, 100), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            d.text((50, 40), "EXIT", fill=(0, 0, 0))
            img_arr = np.array(img)
            result = ocr_reader.readtext(img_arr)
            print("   EasyOCR smoke test passed.")
        except Exception as e:
            print(f"   [ERROR] EasyOCR smoke test failed: {e}")
            all_passed = False
    else:
        all_passed = False

    print("\n===============================")
    if all_passed:
        print("All models ready. Run: python launch.py")
    else:
        print("Finished with errors. Check logs above.")


if __name__ == "__main__":
    main()
