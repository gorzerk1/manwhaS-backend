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

def shift_existing(path, deferred_list):
    tmp = TEMP_DIR / f"defer_{int(time.time()*1000)}_{path.name}"
    path.rename(tmp)
    deferred_list.append((tmp, path.name))

def convert_and_split(image_path, base_index, chapter_path, deferred_list):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size

    if height <= MAX_HEIGHT:
        out_path = chapter_path / f"{base_index:03}.webp"
        if out_path.exists():
            shift_existing(out_path, deferred_list)
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
        if final_path.exists():
            shift_existing(final_path, deferred_list)
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
    deferred = []

    for f in files:
        target_name = f"{idx:03}.webp"
        target_path = chapter / target_name

        if not f.exists():
            continue  # file may have been renamed already

        if f.suffix.lower() == ".webp":
            if target_path.exists() and target_path != f:
                shift_existing(target_path, deferred)
            if f.name != target_name:
                original_mtime = f.stat().st_mtime
                f.rename(target_path)
                os.utime(target_path, (original_mtime, original_mtime))
                log(f"RENAMED: {f.name} → {target_name}")
            else:
                log(f"SKIPPED: {f.name} (already correct)")
            idx += 1

        elif f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            added = convert_and_split(f, idx, chapter, deferred)
            idx += added
            f.unlink()

    for temp_path, original_name in deferred:
        target = chapter / f"{idx:03}.webp"
        original_mtime = temp_path.stat().st_mtime
        temp_path.rename(target)
        os.utime(target, (original_mtime, original_mtime))
        log(f"RENAMED: {temp_path.name} → {target.name}")
        idx += 1

    # ✅ Final clean summary (no false missing)
    webps = sorted(chapter.glob("*.webp"), key=lambda f: f.name)
    log(f"✅ Total .webp files: {len(webps)}")
    log(f"📄 Files: {', '.join(f.name for f in webps)}")

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
