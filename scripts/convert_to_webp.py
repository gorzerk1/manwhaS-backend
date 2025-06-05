import os
import sys
import time
from PIL import Image
from pathlib import Path

ROOT = Path("/home/ubuntu/backend/pictures")
MANWHA = "mookhyang-the-origin"
LOG_DIR = Path("/home/ubuntu/backend/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"{MANWHA}_conversion_{int(time.time())}.log"

WEBP_LIMIT = 16383
converted = 0
skipped = 0
failed = 0
start_size = 0
end_size = 0

def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def folder_size(path):
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

def get_next_number(existing_names):
    i = 1
    while True:
        name = f"{i:03}"
        if name not in existing_names:
            return name
        i += 1

def split_and_convert(img, img_path, chapter_path, base_name):
    global converted, failed

    width, height = img.size
    half = height // 2
    parts = [img.crop((0, 0, width, half)), img.crop((0, half, width, height))]

    for i, part in enumerate(parts):
        new_name = f"{base_name}_{i+1:01}.webp"
        new_path = chapter_path / new_name
        try:
            part.save(new_path, "webp")
            converted += 1
            log(f"SPLIT+CONVERTED: {img_path} → {new_path}")
        except Exception as e:
            failed += 1
            log(f"FAILED SPLIT: {new_path} - {e}")
            continue
    img.close()
    os.remove(img_path)

def convert_image(img_path, chapter_path, used_names):
    global converted, skipped, failed

    try:
        img = Image.open(img_path).convert("RGB")
        width, height = img.size
        base = img_path.stem

        if base in used_names:
            base = get_next_number(used_names)
        used_names.add(base)

        webp_path = chapter_path / f"{base}.webp"
        if webp_path.exists():
            log(f"SKIPPED: {webp_path} already exists")
            img.close()
            skipped += 1
            return

        if max(width, height) > WEBP_LIMIT:
            log(f"SKIPPED (Too Large): {img_path} - {width}x{height} / {WEBP_LIMIT}px limit -> splitting")
            split_and_convert(img, img_path, chapter_path, base)
            return

        img.save(webp_path, "webp")
        img.close()

        if webp_path.exists() and webp_path.stat().st_size > 0:
            os.remove(img_path)
            converted += 1
            log(f"CONVERTED: {img_path} → {webp_path}")
        else:
            failed += 1
            webp_path.unlink(missing_ok=True)
            log(f"FAILED: {img_path}")

    except Exception as e:
        failed += 1
        log(f"ERROR: {img_path} - {e}")

def main():
    global start_size, end_size

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
        images = sorted([p for p in chapter.iterdir() if p.suffix.lower() in [".webp", ".jpg", ".jpeg", ".png"]])
        used_names = set([p.stem for p in images if p.suffix.lower() == ".webp"])

        for img_path in images:
            ext = img_path.suffix.lower()
            if ext == ".webp":
                skipped += 1
                continue
            convert_image(img_path, chapter, used_names)

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
