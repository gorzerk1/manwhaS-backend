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

def get_ordered_images(chapter_path):
    return sorted([
        f for f in chapter_path.iterdir()
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']
    ], key=lambda f: f.name)

def convert_and_split(image_path, base_index, chapter_path):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size

    if height <= MAX_HEIGHT:
        out_path = chapter_path / f"{base_index:03}.webp"
        img.save(out_path, "webp")
        log(f"CONVERTED: {image_path.name} → {out_path.name}")
        return 1

    log(f"SPLITTING: {image_path.name} too tall")
    part_idx = 0
    offset = 0
    count = 0
    while offset < height:
        slice_height = min(MAX_HEIGHT, height - offset)
        part = img.crop((0, offset, width, offset + slice_height))
        temp_path = TEMP_DIR / f"{image_path.stem}-{part_idx}.webp"
        part.save(temp_path, "webp")
        final_path = chapter_path / f"{base_index + count:03}.webp"
        temp_path.rename(final_path)
        log(f"SPLIT+CONVERTED: {image_path.name} → {final_path.name}")
        offset += slice_height
        part_idx += 1
        count += 1
    return count

def process_chapter(chapter):
    log(f"\n📂 {chapter.name}")

    files = get_ordered_images(chapter)
    idx = 1

    for f in files:
        target_name = f"{idx:03}.webp"
        target_path = chapter / target_name

        if f.suffix.lower() == ".webp":
            # Already a webp, just rename if needed
            if f.name != target_name:
                f.rename(target_path)
                log(f"RENAMED: {f.name} → {target_name}")
            else:
                log(f"SKIPPED: {f.name} (already correct)")
            idx += 1

        elif f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            # Convert image (maybe split)
            added = convert_and_split(f, idx, chapter)
            idx += added
            f.unlink()

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
