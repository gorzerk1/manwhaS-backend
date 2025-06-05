import os
import sys
import time
from pathlib import Path
from PIL import Image
from datetime import datetime

MAX_HEIGHT = 16383
ROOT = Path("/home/ubuntu/backend/pictures")
MANWHA = "mookhyang-the-origin"
LOG_DIR = Path("/home/ubuntu/backend/logs/convertToWebLog")
TEMP_DIR = Path("/home/ubuntu/backend/temp")
LOG_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

now = datetime.now().strftime("log_%m-%d-%Y-%H-%M")
LOG_FILE = LOG_DIR / f"{now}.log"

def log(msg):
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    print(f"{timestamp} {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {msg}\n")

def split_image(img: Image.Image) -> list:
    width, height = img.size
    slices = []
    offset = 0
    index = 1
    while offset < height:
        slice_height = min(MAX_HEIGHT, height - offset)
        crop = img.crop((0, offset, width, offset + slice_height))
        out_path = TEMP_DIR / f"split_{index:02}.jpg"
        crop.save(out_path, "JPEG")
        slices.append(out_path)
        offset += slice_height
        index += 1
    return slices

def convert_to_webp(img_path: Path, out_path: Path):
    img = Image.open(img_path).convert("RGB")
    img.save(out_path, "WEBP")
    img.close()

def stitch_images(webp_parts: list, out_path: Path):
    imgs = [Image.open(p).convert("RGB") for p in webp_parts]
    total_height = sum(im.height for im in imgs)
    max_width = max(im.width for im in imgs)
    new_img = Image.new("RGB", (max_width, total_height))

    y = 0
    for im in imgs:
        new_img.paste(im, (0, y))
        y += im.height

    new_img.save(out_path, "WEBP")
    for im in imgs:
        im.close()

def process_chapter(chapter_path: Path):
    items = sorted(chapter_path.glob("*"))
    final_images = []

    for item in items:
        if item.suffix.lower() == ".webp":
            final_images.append(item)
        elif item.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            img = Image.open(item).convert("RGB")
            if img.height <= MAX_HEIGHT:
                out_path = chapter_path / (item.stem + ".webp")
                img.save(out_path, "WEBP")
                log(f"CONVERTED: {item.name} → {out_path.name}")
                final_images.append(out_path)
            else:
                log(f"SPLIT+STITCH: {item.name} too tall")
                slices = split_image(img)
                webp_parts = []
                for slice_img in slices:
                    webp_part = slice_img.with_suffix(".webp")
                    convert_to_webp(slice_img, webp_part)
                    webp_parts.append(webp_part)
                    slice_img.unlink()
                stitched_out = chapter_path / (item.stem + ".webp")
                stitch_images(webp_parts, stitched_out)
                log(f"STITCHED: {item.name} → {stitched_out.name}")
                final_images.append(stitched_out)
                for w in webp_parts:
                    w.unlink()
            img.close()
            item.unlink()

    # Renaming in order
    final_images_sorted = sorted(final_images, key=lambda x: x.name)
    for idx, file in enumerate(final_images_sorted, start=1):
        new_name = f"{idx:03}.webp"
        new_path = chapter_path / new_name
        if file.name != new_name:
            file.rename(new_path)
        log(f"ORDERED: {file.name} → {new_name}")

def main():
    base = ROOT / MANWHA
    if not base.exists():
        log(f"Path not found: {base}")
        sys.exit(1)

    log(f"STARTING: {base}")
    for chapter in sorted(base.glob("chapter-*")):
        if chapter.is_dir():
            log(f"\n📂 {chapter.name}")
            process_chapter(chapter)
    log("\nDONE.")

if __name__ == "__main__":
    main()
