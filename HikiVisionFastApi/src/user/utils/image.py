from PIL import Image
import os
from pathlib import Path

def compress_image_for_hikvision(input_path: str, target_kb: int = 200, step: int = 5, resize_step: float = 0.9) -> str:
    
    img = Image.open(input_path).convert("RGB")

    # Step 1: resize to max resolution
    MAX_WIDTH, MAX_HEIGHT = 1920, 1080
    if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)

    quality = 95
    output_path = str(Path(input_path).with_stem(Path(input_path).stem + "_compressed"))

    while True:
        img.save(output_path, "JPEG", optimize=True, quality=quality)
        size_kb = os.path.getsize(output_path) / 1024

        if size_kb <= target_kb:
            print(f"✅ Compressed to {size_kb:.1f} KB at quality={quality}, size={img.size}")
            break

        if quality > step:
            quality -= step
        else:
            # further resize if still too big
            new_size = (int(img.size[0] * resize_step), int(img.size[1] * resize_step))
            img = img.resize(new_size, Image.LANCZOS)
            quality = 95

    return output_path
