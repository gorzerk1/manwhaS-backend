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

def get_ordered_files(chapter_path):
    return sorted([
        f for f in chapter_path.iterdir()
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']
    ], key=lambda f: f.name)

def clear_temp():
    for f in TEMP_DIR.glob("*"):
        f.unlink()

def convert_image(image_path, base_index):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    out_files = []

    if height <= MAX_HEIGHT:
        temp_out = TEMP_DIR / f"{base_index:03}.webp"
        img.save(temp_out, "webp")
        out_files.append(temp_out)
        log(f"CONVERTED: {image_path.name} → {temp_out.name}")
    else:
        log(f"SPLITTING: {image_path.name} too tall")
        offset = 0
        part_idx = 0
        while offset < height:
            slice_height = min(MAX_HEIGHT, height - offset)
            part = img.crop((0, offset, width, offset + slice_height))
            temp_out = TEMP_DIR / f"{base_index + part_idx:03}.webp"
            part.save(temp_out, "webp")
            log(f"SPLIT+CONVERTED: {image_path.name} → {temp_out.name}")
            out_files.append(temp_out)
            offset += slice_height
            part_idx += 1

    return out_files

def process_chapter(chapter):
    log(f"\n📂 {chapter.name}")
    clear_temp()

    files = get_ordered_files(chapter)

    # Separate by type
    existing_webps = []
    convert_candidates = []

    for f in files:
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            convert_candidates.append(f)
        elif f.suffix.lower() == '.webp':
            existing_webps.append(f)

    # Move convert candidates to TEMP_DIR
    moved_files = []
    for img in convert_candidates:
        target = TEMP_DIR / img.name
        img.rename(target)
        moved_files.append(target)

    # Sort existing .webp by name
    existing_webps.sort(key=lambda f: f.name)
    first_webp = existing_webps[0].name if existing_webps else None

    # Start index
    idx = 1
    output_files = []

    # Convert all moved images
    for temp_img in moved_files:
        converted = convert_image(temp_img, idx)
        output_files.extend(converted)
        idx += len(converted)

    # Now shift original webps
    for old_webp in existing_webps:
        new_name = f"{idx:03}.webp"
        new_path = chapter / new_name
        old_mtime = old_webp.stat().st_mtime
        old_webp.rename(new_path)
        os.utime(new_path, (old_mtime, old_mtime))
        log(f"RENAMED: {old_webp.name} → {new_name}")
        idx += 1

    # Move converted webps back to chapter
    for f in sorted(output_files, key=lambda f: f.name):
        final_name = f.name
        final_path = chapter / final_name
        f.rename(final_path)

    # Log result
    all_webps = sorted(chapter.glob("*.webp"), key=lambda f: f.name)
    log(f"✅ Total .webp files: {len(all_webps)}")
    log(f"📄 Files: {', '.join(f.name for f in all_webps)}")

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
