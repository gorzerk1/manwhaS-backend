import os
import sys
import time
from pathlib import Path
from PIL import Image

MAX_HEIGHT = 16383
ROOT = Path("/home/ubuntu/backend/pictures")
MANWHA = "mookhyang-the-origin"
LOG_DIR = Path("/home/ubuntu/backend/logs/convertToWebLog")
TEMP_DIR = Path("/home/ubuntu/backend/temp")

LOG_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"log_{time.strftime('%-m-%-d-%Y-%H-%M')}.log"

def log(msg):
    timestamp = time.strftime("[%H:%M:%S]")
    print(f"{timestamp} {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {msg}\n")

def get_images(chapter_path):
    return sorted([
        f for f in chapter_path.iterdir()
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']
    ], key=lambda f: f.name)

def split_image(image_path):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    parts = []
    offset = 0
    index = 0
    while offset < height:
        slice_height = min(MAX_HEIGHT, height - offset)
        part = img.crop((0, offset, width, offset + slice_height))
        temp_path = TEMP_DIR / f"{image_path.stem}-{index}.webp"
        part.save(temp_path, "webp")
        parts.append(temp_path)
        offset += slice_height
        index += 1
    img.close()
    return parts

def stitch_images(webp_paths, output_path):
    images = [Image.open(p) for p in webp_paths]
    total_height = sum(img.height for img in images)
    width = images[0].width
    stitched = Image.new("RGB", (width, total_height))

    y_offset = 0
    for img in images:
        stitched.paste(img, (0, y_offset))
        y_offset += img.height

    stitched.save(output_path, "webp")
    for img in images:
        img.close()
    for p in webp_paths:
        p.unlink()

def process_chapter(chapter):
    log(f"\n\U0001F4C2 {chapter.name}")
    files = get_images(chapter)

    for index, file in enumerate(files):
        target_name = f"{index + 1:03}.webp"
        target_path = chapter / target_name

        if file.suffix.lower() == ".webp":
            if file.name != target_name:
                file.rename(target_path)
            log(f"EXISTING: {target_name}")
            continue

        img = Image.open(file).convert("RGB")
        if img.height <= MAX_HEIGHT:
            img.save(target_path, "webp")
            log(f"CONVERTED: {file.name} → {target_name}")
        else:
            log(f"SPLIT+STITCH: {file.name} too tall")
            parts = split_image(file)
            stitch_images(parts, target_path)
            log(f"STITCHED: {file.name} → {target_name}")
        img.close()
        file.unlink()

def main():
    base = ROOT / MANWHA
    if not base.exists():
        print(f"Folder not found: {base}")
        sys.exit(1)

    log(f"STARTING: {base}")
    for chapter in sorted(base.glob("chapter-*")):
        if chapter.is_dir():
            process_chapter(chapter)

if __name__ == "__main__":
    main()
