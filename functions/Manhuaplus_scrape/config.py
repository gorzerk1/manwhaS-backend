import os
import json
from datetime import datetime

# --- PATHS -------------------------------------------------------------
JSON_PATH   = os.path.expanduser("~/server-backend/json/manhwa_list.json")
BASE_DIR    = os.path.expanduser("~/backend")
PICTURES_BASE = os.path.join(BASE_DIR, "pictures")
LOG_BASE      = os.path.join(BASE_DIR, "logs")

# Site we ping before scraping
CHECK_URL   = "https://manhuaplus.org"

# ----------------------------------------------------------------------

def load_manhwa_list() -> list[dict]:
    with open(JSON_PATH, "r", encoding="utf‑8") as f:
        raw = json.load(f)

    manhwa = []
    for name, sources in raw.items():
        for entry in sources:
            if (
                entry.get("site") == "manhuaplus"
                and isinstance(entry.get("url"), str)
                and entry["url"].startswith("https://manhuaplus.org/manga/")
            ):
                manhwa.append({"name": name, "url": entry["url"]})
            else:
                print(f"⚠️  Missing or invalid URL for: {name}")

    return manhwa


def make_log_folder() -> str:
    """Return e.g.  ~/backend/logs/2025‑07‑18_12‑43  (folder created if absent)."""
    stamp = datetime.now().strftime("%Y‑%m‑%d_%H‑%M")
    folder = os.path.join(LOG_BASE, stamp)
    os.makedirs(folder, exist_ok=True)
    return folder
