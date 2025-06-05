import os
from pathlib import Path

BASE_DIR = Path("/home/ubuntu/backend/pictures/mookhyang-the-origin")

def list_chapters(base_dir):
    return sorted([p for p in base_dir.glob("chapter-*") if p.is_dir()])

def list_existing_webps_sorted(chapter_dir):
    return sorted(
        [f.name for f in chapter_dir.glob("*.webp") if f.is_file()]
    )

def main():
    print(f"Checking local images in: {BASE_DIR}\n")
    chapters = list_chapters(BASE_DIR)

    for chapter in chapters:
        print(f"📂 {chapter.name}")
        existing = list_existing_webps_sorted(chapter)

        if not existing:
            print("  ⚠️  No .webp files found.")
            continue

        for f in existing:
            print(f"  OK:   {f}")
        print()

if __name__ == "__main__":
    main()
