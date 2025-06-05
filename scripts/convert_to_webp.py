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

total_before_size = 0
total_after_size = 0

def log(msg):
    timestamp = time.strftime("[%H:%M:%S]")
    print(f"{timestamp} {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {msg}\n")

def get_image_files(chapter_path):
    return sorted([
        f for f in chapter_path.iterdir()
        if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
    ], key=lambda f: f.name)

def move_to_temp(file, index):
    new_path = TEMP_DIR / f"{index:03}_{file.name}"
    file.rename(new_path)
    return new_path

def convert_image(image_path, index_start):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    count = 0
    outputs = []

    if height <= MAX_HEIGHT:
        out_path = TEMP_DIR / f"converted_{index_start:03}.webp"
        img.save(out_path, "webp")
        outputs.append(out_path)
        log(f"CONVERTED: {image_path.name} → {out_path.name}")
        return outputs

    log(f"SPLITTING: {image_path.name} too tall")
    offset = 0
    while offset < height:
        slice_height = min(MAX_HEIGHT, height - offset)
        part = img.crop((0, offset, width, offset + slice_height))
        out_path = TEMP_DIR / f"converted_{index_start + count:03}.webp"
        part.save(out_path, "webp")
        log(f"SPLIT+CONVERTED: {image_path.name} → {out_path.name}")
        outputs.append(out_path)
        offset += slice_height
        count += 1

    return outputs

def get_folder_size(path):
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

def format_size(size_bytes):
    return f"{size_bytes / (1024 ** 3):.2f} GB"

def process_chapter(chapter):
    global total_before_size, total_after_size
    log(f"\n📂 {chapter.name}")
    before_size = get_folder_size(chapter)
    total_before_size += before_size

    files = get_image_files(chapter)
    working_list = []

    for i, f in enumerate(files):
        temp_path = move_to_temp(f, i)
        ext = f.suffix.lower()
        working_list.append({"original": temp_path, "type": ext})

    index = 1
    final_outputs = []
    for entry in working_list:
        if entry["type"] == ".webp":
            target = chapter / f"{index:03}.webp"
            entry["original"].rename(target)
            log(f"MOVED: {entry['original'].name} → {target.name}")
            final_outputs.append(target.name)
            index += 1
        else:
            outputs = convert_image(entry["original"], index)
            for out in outputs:
                target = chapter / f"{index:03}.webp"
                out.rename(target)
                final_outputs.append(target.name)
                index += 1

    after_size = get_folder_size(chapter)
    total_after_size += after_size
    saved = before_size - after_size
    percent_saved = (saved / before_size * 100) if before_size > 0 else 0

    log(f"✅ Total .webp files: {len(final_outputs)}")
    log(f"📄 Files: {', '.join(final_outputs)}")
    log(f"📦 Size before: {format_size(before_size)} → after: {format_size(after_size)}")
    log(f"📮 Saved: {format_size(saved)} ({percent_saved:.2f}%)")

def main():
    base = ROOT / MANWHA
    if not base.exists():
        print(f"Folder not found: {base}")
        sys.exit(1)

    log(f"STARTING: {base}")
    for chapter in sorted(base.glob("chapter-*")):
        if chapter.is_dir():
            process_chapter(chapter)

    total_saved = total_before_size - total_after_size
    percent_total = (total_saved / total_before_size * 100) if total_before_size > 0 else 0
    log("\n===== OVERALL SUMMARY =====")
    log(f"📦 Total size before: {format_size(total_before_size)}")
    log(f"📆 Total size after: {format_size(total_after_size)}")
    log(f"📢 Total saved: {format_size(total_saved)} ({percent_total:.2f}%)")

if __name__ == "__main__":
    main()
