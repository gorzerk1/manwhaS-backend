import os
import re
import time
from pathlib import Path

BASE_PATH = Path("/home/ubuntu/backend/pictures/mookhyang-the-origin")
LOG_DIR = Path("/home/ubuntu/backend/logs/isImageValid")
LOG_DIR.mkdir(parents=True, exist_ok=True)  # Make sure the folder exists
LOG_FILE = LOG_DIR / f"log_{int(time.time())}.log"

def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def extract_number(filename):
    match = re.match(r"(\d+)\.webp$", filename)
    return int(match.group(1)) if match else None

def check_chapter(chapter_path):
    log(f"\n📂 {chapter_path.name}")
    files = [f.name for f in chapter_path.iterdir() if f.suffix == '.webp']
    numbers = sorted(filter(None, (extract_number(f) for f in files)))

    if not numbers:
        log("  (no .webp files)")
        return

    min_num = min(numbers)
    max_num = max(numbers)
    existing = set(numbers)

    for i in range(min_num, max_num + 1):
        filename = f"{i:03}.webp"
        if i in existing:
            log(f"  OK:     {filename}")
        else:
            log(f"  MISSING: {filename}")

def main():
    for chapter in sorted(BASE_PATH.glob("chapter-*")):
        if chapter.is_dir():
            check_chapter(chapter)

if __name__ == "__main__":
    main()
