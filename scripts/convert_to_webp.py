import os
import sys
import time
from PIL import Image
from pathlib import Path

ROOT = Path("/home/ubuntu/backend/pictures")
MANWHA = "mookhyang-the-origin"  # change if needed
LOG_DIR = Path("/home/ubuntu/backend/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"{MANWHA}_conversion_{int(time.time())}.log"

converted = 0
skipped = 0
failed = 0
start_size = 0
end_size = 0
WEBP_MAX = 16383

def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def folder_size(path):
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

def convert_image(image_path):
    global converted, failed

    try:
        img = Image.open(image_path).convert("RGB")
        width, height = img.size

        if width > WEBP_MAX or height > WEBP_MAX:
            failed += 1
            log(f"SKIPPED (Too Large): {image_path} - {width}x{height} / {WEBP_MAX}px limit")
            return

        webp_path = image_path.with_suffix(".webp")
        if webp_path.exists():
            log(f"SKIPPED: {webp_path} already exists")
            return

        img.save(webp_path, "webp")
        img.close()

        if webp_path.exists() and webp_path.stat().st_size > 0:
            os.remove(image_path)
            converted += 1
            log(f"CONVERTED: {image_path} → {webp_path}")
        else:
            failed += 1
            webp_path.unlink(missing_ok=True)
            log(f"FAILED (Empty webp): {image_path}")
    except Exception as e:
        failed += 1
        log(f"ERROR: {image_path} - {e}")

def main():
    global start_size, end_size, skipped

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
        for img_path in chapter.rglob("*"):
            if img_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                convert_image(img_path)
            elif img_path.suffix.lower() == ".webp":
                skipped += 1

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
