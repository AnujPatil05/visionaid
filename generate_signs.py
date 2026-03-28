import os
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    font_names = ["nirmalab.ttf", "arialbd.ttf", "arial.ttf", "segoeui.ttf"]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except IOError:
            continue
    return ImageFont.load_default()

def create_sign(filename, text, bg_color):
    width, height = 1654, 2339
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    font = get_font(200)
    
    # Intelligently split the dual-language or long signs onto multiple lines
    parts = text.split(" / ")
    display_text = "\n".join(parts)
    
    if text == "CAUTION: WET FLOOR":
        display_text = "CAUTION:\nWET FLOOR"
        
    try:
        draw.multiline_text((width/2, height/2), display_text, fill=(0,0,0), font=font, anchor="mm", align="center")
    except AttributeError:
        # Fallback for earlier PIL setups
        bbox = draw.textbbox((0,0), display_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.multiline_text(((width-text_w)/2, (height-text_h)/2), display_text, fill=(0,0,0), font=font, align="center")

    os.makedirs("demo_assets/signs", exist_ok=True)
    out_path = os.path.join("demo_assets/signs", filename)
    img.save(out_path)
    
    size_kb = os.path.getsize(out_path) / 1024
    print(f"Saved {out_path} ({size_kb:.1f} KB)")

def main():
    signs = [
        ("sign_01.png", "EMERGENCY EXIT ->", (255, 255, 255)),
        ("sign_02.png", "प्रवेश निषेध / NO ENTRY", (255, 255, 255)),
        ("sign_03.png", "CAUTION: WET FLOOR", (255, 255, 0)),
        ("sign_04.png", "PLATFORM 3 ->", (255, 255, 255)),
        ("sign_05.png", "PHARMACY / औषधालय", (255, 255, 255)),
    ]
    
    for filename, text, color in signs:
        create_sign(filename, text, color)
        
    print("\nPrint at A4, 100% scale, no fit-to-page.")

if __name__ == "__main__":
    main()
