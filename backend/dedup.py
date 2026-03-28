import time
import difflib
import threading

_spoken: dict[str, float] = {}   # text -> timestamp
_lock = threading.Lock()


def should_speak(text: str, cooldown: float = 5.0) -> bool:
    """
    Return True if the text (or anything fuzzy-similar to it) has NOT
    been spoken within the cooldown window.

    Fuzzy match: uses difflib.SequenceMatcher ratio > 0.75 against every
    entry currently in the cooldown window.  This prevents OCR jitter
    ("EMERGENCY EXIT" vs "EMERGENCY EXJT") from causing repeat reads.
    """
    now = time.time()
    text_lower = text.lower().strip()

    with _lock:
        # Prune expired entries to keep dict from growing forever
        expired = [k for k, t in _spoken.items() if now - t >= cooldown]
        for k in expired:
            del _spoken[k]

        # Check for fuzzy similarity against currently active entries
        for existing_text in _spoken:
            ratio = difflib.SequenceMatcher(
                None, text_lower, existing_text
            ).ratio()
            if ratio > 0.75:
                return False  # Similar enough — skip

        # New or expired — record and allow
        _spoken[text_lower] = now
        return True
