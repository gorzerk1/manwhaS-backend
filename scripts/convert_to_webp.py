import os
import sys
import time
import json
from pathlib import Path
from PIL import Image, UnidentifiedImageError

MAX_HEIGHT = 16383
ROOT = Path("/home/ubuntu/backend/pictures")
LOG_DIR = Path("/home/ubuntu/backend/logs/convertToWebLog")
TEMP_DIR = Path("/home/ubuntu/backend/temp")
MANHWA_LIST_JSON = Path("/home/ubuntu/backend/json/manhwa_list.json")

LOG_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"log_{time.strftime('%-m-%-d-%Y-%H-%M')}.log"

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

def convert_image(image_path, index_start, chapter_name):
    try:
        img = Image.open(image_path).convert("RGB")
    except UnidentifiedImageError:
        log(f"❌ CORRUPT: {chapter_name} > {image_path.name}")
        return []
    except Exception as e:
        log(f"❌ ERROR: {chapter_name} > {image_path.name} ({e})")
        return []

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

def process_chapter(chapter, summary):
    files = get_image_files(chapter)
    if all(f.suffix.lower() == ".webp" for f in files):
        log(f"⏭️ SKIPPED: {chapter.name} (all files are .webp)")
        return

    log(f"\n📂 {chapter.name}")
    before_size = get_folder_size(chapter)
    summary["before"] += before_size

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
            final_outputs.append(target.name)
            index += 1
        else:
            outputs = convert_image(entry["original"], index, chapter.name)
            for out in outputs:
                target = chapter / f"{index:03}.webp"
                out.rename(target)
                final_outputs.append(target.name)
                index += 1

    after_size = get_folder_size(chapter)
    summary["after"] += after_size

    log(f"✅ Total .webp files: {len(final_outputs)}")
    log(f"📄 Files: {', '.join(final_outputs)}")

def main():
    if not MANHWA_LIST_JSON.exists():
        print(f"File not found: {MANHWA_LIST_JSON}")
        sys.exit(1)

    with open(MANHWA_LIST_JSON) as f:
        manhwa_list = json.load(f)

    summary_list = []

    for manhwa_name in sorted(manhwa_list.keys()):
        base = ROOT / manhwa_name
        if not base.exists():
            log(f"🚫 MISSING: {base}")
            continue

        log(f"\n=== STARTING: {manhwa_name} ===")
        summary = {"name": manhwa_name, "before": 0, "after": 0}

        for chapter in sorted(base.glob("chapter-*"), key=lambda x: int(x.name.split("-")[-1])):
            if chapter.is_dir():
                process_chapter(chapter, summary)

        summary_list.append(summary)

    log("\n====== FINAL SUMMARY ======")
    for s in summary_list:
        saved = s["before"] - s["after"]
        percent = (saved / s["before"] * 100) if s["before"] > 0 else 0
        log(f"\n{s['name']} :")
        log(f"📦 Total size before: {format_size(s['before'])}")
        log(f"📆 Total size after: {format_size(s['after'])}")
        log(f"📢 Total saved: {format_size(saved)} ({percent:.2f}%)")

if __name__ == "__main__":
    main()
