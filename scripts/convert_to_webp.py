import os
import sys
import time
from pathlib import Path
from PIL import Image
from datetime import datetime

MAX_HEIGHT = 16383
ROOT = Path("/home/ubuntu/backend/pictures")
MANWHA = "mookhyang-the-origin"

# Fixed log directory and naming
LOG_DIR = Path("/home/ubuntu/backend/logs/convertToWebLog")
LOG_DIR.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = LOG_DIR / f"{MANWHA}_conversion_{timestamp}.log"

converted = 0
skipped = 0
failed = 0

def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def folder_size(path):
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

def split_and_save(img, base_name, chapter_path, counter):
    width, height = img.size
    parts = []
    offset = 0
    while offset < height:
        slice_height = min(MAX_HEIGHT, height - offset)
        part = img.crop((0, offset, width, offset + slice_height))
        file_name = f"{counter:03}.webp"
        out_path = chapter_path / file_name
        part.save(out_path, "webp")
        parts.append(out_path)
        log(f"SPLIT+CONVERTED: {base_name} → {file_name}")
        offset += slice_height
        counter += 1
    return parts, counter

def convert_and_rename(chapter_path):
    global converted, skipped, failed
    files = sorted(
        [f for f in chapter_path.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]],
        key=lambda x: x.name
    )

    # FIXED: start counter based on existing webp files
    existing_webps = sorted([f for f in chapter_path.glob("*.webp")])
    counter = len(existing_webps) + 1

    for file in files:
        ext = file.suffix.lower()
        if ext == ".webp":
            expected_name = f"{counter:03}.webp"
            new_path = chapter_path / expected_name
            if file.name != expected_name:
                file.rename(new_path)
            log(f"EXISTING: {expected_name}")
            counter += 1
            skipped += 1
            continue

        try:
            img = Image.open(file).convert("RGB")
            width, height = img.size

            if height > MAX_HEIGHT:
                log(f"SPLIT: {file} - {width}x{height}")
                parts, counter = split_and_save(img, file.name, chapter_path, counter)
                converted += len(parts)
            else:
                out_path = chapter_path / f"{counter:03}.webp"
                img.save(out_path, "webp")
                log(f"CONVERTED: {file.name} → {out_path.name}")
                counter += 1
                converted += 1

            img.close()
            file.unlink()
        except Exception as e:
            failed += 1
            log(f"ERROR: {file} - {e}")

def main():
    global converted, skipped, failed
    base = ROOT / MANWHA
    if not base.exists():
        print(f"Folder not found: {base}")
        sys.exit(1)

    log(f"Starting conversion in: {base}")
    start_size = folder_size(base)

    for chapter in sorted(base.glob("chapter-*")):
        if not chapter.is_dir():
            continue
        log(f"\nProcessing {chapter}")
        convert_and_rename(chapter)

    end_size = folder_size(base)
    saved = start_size - end_size

    log("\n=== SUMMARY ===")
    log(f"Total before: {start_size / 1024 / 1024:.2f} MB")
    log(f"Total after:  {end_size / 1024 / 1024:.2f} MB")
    log(f"Saved:       {saved / 1024 / 1024:.2f} MB")
    log(f"Converted:   {converted}")
    log(f"Skipped:     {skipped}")
    log(f"Failed:      {failed}")

if __name__ == "__main__":
    main()
