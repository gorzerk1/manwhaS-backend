import os
import sys
from pathlib import Path
from PIL import Image
from datetime import datetime

MAX_HEIGHT = 16383
ROOT = Path("/home/ubuntu/backend/pictures")
MANWHA = "mookhyang-the-origin"

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

def process_image(file, output_dir, counter):
    global converted, failed
    try:
        img = Image.open(file).convert("RGB")
        width, height = img.size

        if height > MAX_HEIGHT:
            log(f"SPLIT: {file.name} - {width}x{height}")
            offset = 0
            while offset < height:
                slice_height = min(MAX_HEIGHT, height - offset)
                part = img.crop((0, offset, width, offset + slice_height))
                out_path = output_dir / f"{counter:03}.webp"
                part.save(out_path, "webp")
                log(f"CONVERTED: {file.name} → {out_path.name}")
                counter += 1
                converted += 1
                offset += slice_height
        else:
            out_path = output_dir / f"{counter:03}.webp"
            img.save(out_path, "webp")
            log(f"CONVERTED: {file.name} → {out_path.name}")
            counter += 1
            converted += 1

        img.close()
        file.unlink()
    except Exception as e:
        failed += 1
        log(f"ERROR: {file.name} - {e}")
    return counter

def process_chapter(chapter_path):
    global skipped

    files = sorted(
        [f for f in chapter_path.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]],
        key=lambda x: x.name
    )

    counter = 1

    for file in files:
        ext = file.suffix.lower()
        if ext == ".webp":
            new_name = f"{counter:03}.webp"
            new_path = chapter_path / new_name
            if file.name != new_name:
                file.rename(new_path)
                log(f"RENAMED: {file.name} → {new_name}")
            else:
                log(f"KEPT: {file.name}")
            counter += 1
            skipped += 1
        else:
            counter = process_image(file, chapter_path, counter)

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
        process_chapter(chapter)

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
