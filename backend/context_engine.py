import re

DANGER_KEYWORDS = ['danger', 'warning', 'caution', 'hazard', 'खतरा', 'चेतावनी', 'सावधान']

SIGN_MAP = {
    # English
    'stop': ("Stop sign detected. Please halt.", True),
    'no entry': ("No entry. Do not proceed.", True),
    'exit': ("Exit sign detected.", False),
    'emergency exit': ("Emergency exit nearby.", False),
    'caution': ("Caution! Potential hazard nearby.", True),
    'danger': ("Danger! Please stop and be careful.", True),
    'wet floor': ("Wet floor warning. Risk of slipping.", True),
    'pharmacy': ("Pharmacy detected.", False),
    'hospital': ("Hospital zone.", False),
    'toilet': ("Restroom nearby.", False),
    'platform 3': ("Platform 3 ahead. Watch the gap.", False),
    'platform': ("Platform ahead. Watch the gap.", False),
    'fire exit': ("Fire exit located here.", True),
    'school': ("School zone. Be careful.", True),
    'push': ("Push the door.", False),
    'pull': ("Pull the door.", False),
    'atm': ("ATM machine nearby.", False),
    'gate': ("Gate detected nearby.", False),
    'parking': ("Parking area nearby.", False),
    'bank': ("Bank detected ahead.", False),
    'no smoking': ("No smoking zone.", False),
    # Hindi
    'प्रवेश निषेध': ("No entry. Do not proceed.", True),
    'रुकें': ("Stop sign detected. Please halt.", True),
    'खतरा': ("Danger! Please stop and be careful.", True),
    'निकास': ("Exit sign detected.", False),
    'अस्पताल': ("Hospital zone.", False),
    'शौचालय': ("Restroom nearby.", False),
    'औषधालय': ("Pharmacy detected.", False)
}

def build_speech(raw_text: str, spatial: dict) -> tuple[str, bool]:
    raw_lower = raw_text.lower()
    
    distance = spatial.get('distance_label', '')
    direction = spatial.get('direction', '')
    
    # Determine arrows dynamically
    append_speech = ""
    if '->' in raw_lower or 'right' in raw_lower:
        append_speech = " Turn right."
    elif '<-' in raw_lower or 'left' in raw_lower:
        append_speech = " Turn left."
        
    # Check SIGN_MAP mappings based on verbatim matching
    for key, (template, is_danger) in SIGN_MAP.items():
        if key in raw_lower:
            speech = f"{template} {distance.capitalize()}, {direction}."
            speech += append_speech
            return speech, is_danger
            
    # Check general DANGER_KEYWORDS
    is_danger = any(keyword in raw_lower for keyword in DANGER_KEYWORDS)
    
    # Fallback to pure OCR reading -> Clean text first by stripping unknown tokens
    clean = re.sub(r'[^a-zA-Z0-9\s\u0900-\u097F]', '', raw_text)
    
    # Prevent duplicated "Exit right. Turn right." readings from arrows that have explicit textual directions
    clean = re.sub(r'(?i)\b(?:right|left)\b', '', clean).strip()
    
    if not clean:
        clean = "General sign"
        
    speech = f"Sign reads: {clean}. {distance.capitalize()}, {direction}."
    speech += append_speech
        
    return speech, is_danger
