from pathlib import Path
import re

BASE_DIR = Path("/home/ubuntu/backend/pictures/mookhyang-the-origin")

def list_chapters(base_dir):
    return sorted([
        p for p in base_dir.iterdir()
        if p.is_dir() and re.match(r"chapter-\d+", p.name)
    ])

def list_expected_images(chapter_dir, max_count=100):
    # Assumes files like 001.webp, 002.webp, ..., up to max_count
    return [f"{str(i).zfill(3)}.webp" for i in range(1, max_count + 1)]

def check_image_exists(chapter_path, filename):
    return (chapter_path / filename).exists()

def main():
    print(f"Checking local images in: {BASE_DIR}\n")
    chapters = list_chapters(BASE_DIR)

    for chapter in chapters:
        print(f"📂 {chapter.name}")
        expected_files = list_expected_images(chapter)
        for fname in expected_files:
            if check_image_exists(chapter, fname):
                print(f"  OK:   {fname}")
            else:
                print(f"  MISSING: {fname}")
        print()

if __name__ == "__main__":
    main()
