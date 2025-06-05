import os
import re
from pathlib import Path

BASE_PATH = Path("/home/ubuntu/backend/pictures/mookhyang-the-origin")

def extract_number(filename):
    match = re.match(r"(\d+)\.webp$", filename)
    return int(match.group(1)) if match else None

def check_chapter(chapter_path):
    print(f"\n📂 {chapter_path.name}")

    files = [f.name for f in chapter_path.iterdir() if f.suffix == '.webp']
    numbers = sorted(filter(None, (extract_number(f) for f in files)))

    if not numbers:
        print("  (no .webp files)")
        return

    min_num = min(numbers)
    max_num = max(numbers)
    existing = set(numbers)

    for i in range(min_num, max_num + 1):
        filename = f"{i:03}.webp"
        if i in existing:
            print(f"  OK:   {filename}")
        else:
            print(f"  MISSING: {filename}")

def main():
    for chapter in sorted(BASE_PATH.glob("chapter-*")):
        if chapter.is_dir():
            check_chapter(chapter)

if __name__ == "__main__":
    main()
