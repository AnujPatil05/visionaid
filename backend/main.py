import cv2
import numpy as np
import socket
import qrcode
import io
import asyncio

import uvicorn
import traceback
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from detector import detect_signs, sharpness_score, scene_summary, scan_qr
from ocr_engine import extract_text
from spatial import get_spatial_cue
from dedup import should_speak
from context_engine import build_speech

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_frame_count = 0
_frame_buffer = []
_buffer_lock = asyncio.Lock()

@app.get("/health")
def health():
    return {"status": "ok", "frame_count": _frame_count}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

@app.get("/qrcode")
def get_qr():
    ip = get_local_ip()
    url = f"http://{ip}:8000"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@app.post("/process")
async def process(file: UploadFile = File(...)):
    try:
        global _frame_count, _frame_buffer
        _frame_count += 1

        frame_bytes = await file.read()

        # --- QR code fast-path (before YOLO/OCR pipeline) ---
        qr_data = scan_qr(frame_bytes)
        if qr_data:
            speech = f"QR code detected. It says: {qr_data}"
            if should_speak(f"qr:{qr_data}"):
                return {
                    "action": "spoken",
                    "speech": speech,
                    "is_danger": False,
                    "direction": "ahead",
                    "lang": "en",
                    "ocr_confidence": 1.0
                }
            else:
                return {"action": "dedup"}

        # --- Sharpness-based frame buffering ---
        np_arr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"action": "none"}

        sharpness = sharpness_score(frame)
        _frame_buffer.append((sharpness, frame_bytes))

        if len(_frame_buffer) < 3:
            return {"action": "buffering", "count": len(_frame_buffer)}

        best_sharpness, best_frame_bytes = max(_frame_buffer, key=lambda x: x[0])
        _frame_buffer.clear()

        # --- Sign detection + OCR pipeline ---
        detections = detect_signs(best_frame_bytes)
        if not detections:
            return {"action": "none"}

        best = max(detections, key=lambda d: d['confidence'])

        text, lang, ocr_conf = extract_text(best['cropped'])
        if not text or ocr_conf < 0.20:
            return {"action": "low_confidence"}

        spatial = get_spatial_cue(best['bbox'], best['frame_size'])
        speech, is_danger = build_speech(text, spatial)

        if should_speak(text):
            return {
                "action": "spoken",
                "speech": speech,
                "is_danger": is_danger,
                "direction": spatial['direction'],
                "lang": lang,
                "ocr_confidence": round(float(ocr_conf), 2),
                "bbox_height": round(
                    (best['bbox'][3] - best['bbox'][1]) / best['frame_size'][1], 3
                )
            }
        else:
            return {"action": "dedup"}

    except Exception as e:
        print("INTERNAL SERVER CRASH TRACE:")
        print(traceback.format_exc())
        return {"action": "error", "message": traceback.format_exc()}


@app.post("/scene")
async def scene(file: UploadFile = File(...)):
    """Return a natural-language description of everything visible in the frame."""
    try:
        frame_bytes = await file.read()
        summary = scene_summary(frame_bytes)
        return {"summary": summary}
    except Exception as e:
        print("SCENE ENDPOINT ERROR:")
        print(traceback.format_exc())
        return {"summary": "Could not analyse the scene."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
