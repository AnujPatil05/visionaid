import easyocr

# Initialize once (GLOBAL)
reader = easyocr.Reader(['en', 'hi'], gpu=False)

def extract_text(image):
    try:
        results = reader.readtext(image)

        if not results:
            return "", "unknown", 0.0

        # Calculate physical bounding box height: bottom-right Y minus top-left Y
        def box_height(r):
            try:
                return abs(r[0][2][1] - r[0][0][1])
            except:
                return 0
                
        # Sort aggressively by largest text on the screen, ignore background noise
        results.sort(key=box_height, reverse=True)
        
        valid_results = [r for r in results if r[2] > 0.05]
        if not valid_results:
            print("EASYOCR SAW NOTHING OR LOW CONFIDENCE")
            return "", "unknown", 0.0

        # String together the massive text components
        text = " ".join([r[1] for r in valid_results])
        conf = float(sum(r[2] for r in valid_results) / len(valid_results))
        print(f"EASYOCR DETECTED: '{text}' w/ conf: {conf}")

        # Simple language detection
        if any('\u0900' <= c <= '\u097F' for c in text):
            lang = "hi"
        else:
            lang = "en"

        return text, lang, conf

    except Exception as e:
        print(f"[OCR ERROR] {e}")
        return "", "unknown", 0.0
