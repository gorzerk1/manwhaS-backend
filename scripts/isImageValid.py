import os
import re
import time
from datetime import datetime
from pathlib import Path

BASE_PATH = Path("/home/ubuntu/backend/pictures/mookhyang-the-origin")
LOG_DIR = Path("/home/ubuntu/backend/logs/isImageValid")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Create log file with format: log_6-5-2025-16-22.log
now = datetime.now()
timestamp = now.strftime("log_%-m-%-d-%Y-%H-%M.log")  # For Linux. Use "%#m" if on Windows.
LOG_FILE = LOG_DIR / timestamp

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
