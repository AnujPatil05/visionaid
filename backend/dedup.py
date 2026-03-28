import time
import hashlib
import threading

_spoken = {}
_lock = threading.Lock()

def should_speak(text, cooldown=5.0) -> bool:
    text_hash = hashlib.md5(text.lower().encode('utf-8')).hexdigest()
    now = time.time()
    
    with _lock:
        if text_hash in _spoken:
            if now - _spoken[text_hash] < cooldown:
                return False
        
        _spoken[text_hash] = now
        return True
