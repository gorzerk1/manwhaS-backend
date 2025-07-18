import os
import re
from pathlib import Path
from typing import Optional

# ── Asura has an extra check inside each chapter folder ───────────────────────
def get_asura_latest_chapter(folder_path: Path) -> Optional[int]:
    chapters = sorted(
        [
            int(m.group(1))
            for m in (
                re.match(r"chapter-(\d+)", d) for d in os.listdir(folder_path)
            )
            if m
        ],
        reverse=True,
    )

    for chap_num in chapters:
        source_file = folder_path / f"chapter-{chap_num}" / "source.txt"
        if source_file.exists():
            if "Downloaded from AsuraScans" in source_file.read_text(errors="ignore"):
                return chap_num
    return None


def get_local_latest_chapter(folder_path: Path) -> Optional[int]:
    chapter_nums = []
    for name in os.listdir(folder_path):
        m = re.match(r"chapter-(\d+)", name.lower())
        if m:
            chapter_nums.append(int(m.group(1)))
    return max(chapter_nums) if chapter_nums else None
