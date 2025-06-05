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

def split_image(img, base_name):
    width, height = img.size
    parts = []
    offset = 0
    while offset < height:
        slice_height = min(MAX_HEIGHT, height - offset)
        part = img.crop((0, offset, width, offset + slice_height))
        parts.append(part)
        offset += slice_height
    return parts

def convert_and_collect(chapter_path):
    global converted, skipped, failed

    files = sorted(
        [f for f in chapter_path.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]],
        key=lambda x: x.name
    )

    temp_files = []  # list of tuples (Image, source_name) OR (Path, None)

    for file in files:
        ext = file.suffix.lower()
        if ext == ".webp":
            temp_files.append((file, None))  # just keep it for final rename
            log(f"EXISTING: {file.name}")
            skipped += 1
        else:
            try:
                img = Image.open(file).convert("RGB")
                if img.height > MAX_HEIGHT:
                    log(f"SPLIT: {file.name} - {img.width}x{img.height}")
                    parts = split_image(img, file.name)
                    for part in parts:
                        temp_files.append((part, file.name))
                        converted += 1
                else:
                    temp_files.append((img, file.name))
                    converted += 1
                img.close()
                file.unlink()
            except Exception as e:
                failed += 1
                log(f"ERROR: {file} - {e}")

    # remove all existing .webp so we reassign names in clean order
    for f in chapter_path.glob("*.webp"):
        f.unlink()

    # save everything in final order
    for idx, (entry, source_name) in enumerate(temp_files, start=1):
        out_name = f"{idx:03}.webp"
        out_path = chapter_path / out_name
        if isinstance(entry, Path):
            entry.rename(out_path)
            log(f"RENAMED: {entry.name} → {out_name}")
        else:
            entry.save(out_path, "webp")
            log(f"CONVERTED: {source_name} → {out_name}")

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
        convert_and_collect(chapter)

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
