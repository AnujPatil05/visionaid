import os
import cv2
import numpy as np
from collections import Counter
from ultralytics import YOLO

_model = None

# Always resolve model path relative to this file, regardless of CWD
_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yolo11n.pt')


def get_model():
    global _model
    if _model is None:
        # 'yolo11n.pt' — ultralytics will auto-download if file not on disk yet
        _model = YOLO(_MODEL_PATH if os.path.exists(_MODEL_PATH) else 'yolo11n.pt')
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

        # Crop sign region with 10px padding (clamped to frame bounds)
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
        # Fallback: YOLO missed a purely-text sign — send full frame to OCR
        detections.append({
            'bbox': (0, 0, w, h),
            'frame_size': (w, h),
            'confidence': 0.99,
            'label': 'full_scan_fallback',
            'cropped': frame
        })

    return detections


def scene_summary(frame_bytes: bytes) -> str:
    """
    Describe what YOLO can see in a single natural-language sentence.
    Uses the already-loaded YOLO singleton — no extra model download.

    Returns e.g.: "Around you: 2 people ahead, 1 chair to your left."
    If nothing is detected: "The area appears clear."
    Capped at the top 4 most common object classes to keep speech short.
    """
    np_arr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        return "Cannot see anything right now."

    model = get_model()
    h, w = frame.shape[:2]

    results = model(frame, conf=0.35, verbose=False)[0]

    if not results.boxes or len(results.boxes) == 0:
        return "The area appears clear."

    # Count objects and track the dominant position of each class
    label_counts: Counter = Counter()
    label_positions: dict[str, str] = {}

    for box in results.boxes:
        label_idx = int(box.cls[0])
        label = model.names[label_idx] if hasattr(model, 'names') else str(label_idx)
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        cx = (x1 + x2) / 2

        if cx < w / 3:
            pos = "to your left"
        elif cx > 2 * w / 3:
            pos = "to your right"
        else:
            pos = "ahead"

        label_counts[label] += 1
        # Keep the position of the most-central / first-seen instance per class
        if label not in label_positions:
            label_positions[label] = pos

    # Build sentence from top 4 classes
    parts = []
    for label, count in label_counts.most_common(4):
        pos = label_positions.get(label, "nearby")
        noun = label.replace("_", " ")
        plural = "s" if count > 1 else ""
        parts.append(f"{count} {noun}{plural} {pos}")

    if not parts:
        return "The area appears clear."

    return "Around you: " + ", ".join(parts) + "."


def scan_qr(frame_bytes: bytes) -> str | None:
    """
    Detect and decode a QR code in the frame using OpenCV's built-in
    QRCodeDetector — no extra dependencies.

    Returns the decoded string (truncated to 80 chars) or None.
    """
    np_arr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        return None

    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(frame)

    if data:
        return data[:80]  # truncate long URLs to keep TTS readable
    return None
