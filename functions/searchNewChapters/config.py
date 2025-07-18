import json
import os
from pathlib import Path

# ── absolute paths ────────────────────────────────────────────────────────────
json_path   = Path("/home/ubuntu/server-backend/json/manhwa_list.json")
pictures_path = Path("~/backend/pictures").expanduser()
log_dir       = Path("~/backend/logs/searchNewChapters").expanduser()

# ── tiny helpers ──────────────────────────────────────────────────────────────
def load_manhwa_list() -> dict:
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_manhwa_list(data: dict) -> None:
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
