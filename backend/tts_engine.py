import pyttsx3
import threading

_engine = None
_lock = threading.Lock()

def get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty('rate', 160)
        _engine.setProperty('volume', 1.0)
    return _engine

def _speak_thread(text, danger):
    with _lock:
        engine = get_engine()
        if danger:
            engine.setProperty('rate', 130)
        else:
            engine.setProperty('rate', 160)
            
        engine.say(text)
        engine.runAndWait()

def speak(text, danger=False):
    t = threading.Thread(target=_speak_thread, args=(text, danger), daemon=True)
    t.start()
