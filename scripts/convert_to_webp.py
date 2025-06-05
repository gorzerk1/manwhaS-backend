import os
import sys
import time
from PIL import Image
from pathlib import Path

MAX_WEBP_HEIGHT = 16383

ROOT = Path("/home/ubuntu/backend/pictures")
MANWHA = "mookhyang-the-origin"
LOG_DIR = Path("/home/ubuntu/backend/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"{MANWHA}_conversion_{int(time.time())}.log"

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

def convert_image(image_path):
    global converted, failed

    try:
        img = Image.open(image_path).convert("RGB")
        width, height = img.size

        if height > MAX_WEBP_HEIGHT:
            log(f"SKIPPED (Too Large): {image_path} - {width}x{height} / {MAX_WEBP_HEIGHT}px limit -> splitting")

            mid = height // 2
            top = img.crop((0, 0, width, mid))
            bottom = img.crop((0, mid, width, height))

            base_name = image_path.stem
            parent = image_path.parent

            out1 = parent / f"{base_name}_1.webp"
            out2 = parent / f"{base_name}_2.webp"

            top.save(out1, "webp")
            bottom.save(out2, "webp")

            top.close()
            bottom.close()
            img.close()

            if out1.exists() and out2.exists():
                os.remove(image_path)
                converted += 2
                log(f"SPLIT+CONVERTED: {image_path} → {out1}")
                log(f"SPLIT+CONVERTED: {image_path} → {out2}")
            else:
                failed += 1
                log(f"FAILED: Split save failed for {image_path}")
            return

        # Normal conversion
        webp_path = image_path.with_suffix(".webp")
        if webp_path.exists():
            log(f"SKIPPED (Already WebP): {webp_path}")
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
            log(f"FAILED: {image_path}")

    except Exception as e:
        failed += 1
        log(f"ERROR: {image_path} - {e}")

def main():
    global start_size, end_size, skipped, converted, failed

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
        files = sorted(chapter.glob("*"))
        for img_path in files:
            ext = img_path.suffix.lower()
            if ext in [".jpg", ".jpeg", ".png"]:
                convert_image(img_path)
            elif ext == ".webp":
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
