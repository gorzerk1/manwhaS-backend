import os
import json
from datetime import datetime

# === CONFIG ===
mawha_base_path = "/home/ubuntu/backend/pictures"
base_output_dir = "/home/ubuntu/backend/data/jsonFiles"
details_path = "/home/ubuntu/server-backend/json/manwha_details.json"

# === Load details JSON ===
if os.path.exists(details_path):
    with open(details_path, "r", encoding="utf-8") as f:
        manwha_details = json.load(f)
else:
    print("⚠️ manwha_details.json not found — continuing with empty details.")
    manwha_details = {}

# === Ensure output dir exists ===
os.makedirs(base_output_dir, exist_ok=True)

# === Scan manhwa folders ===
for manhwa_name in os.listdir(mawha_base_path):
    manhwa_path = os.path.join(mawha_base_path, manhwa_name)
    if not os.path.isdir(manhwa_path):
        continue

    manhwa_output_dir = os.path.join(base_output_dir, manhwa_name)
    os.makedirs(manhwa_output_dir, exist_ok=True)

    # === Get chapters ===
    chapter_folders = sorted(
        [f for f in os.listdir(manhwa_path) if f.startswith("chapter-")],
        key=lambda x: int(x.replace("chapter-", ""))
    )
    chapters_amount = max([int(f.replace("chapter-", "")) for f in chapter_folders], default=0)

    # === Get details or fallback ===
    details = manwha_details.get(manhwa_name, {})
    description = {
        "imagelogo": f"backend/manwhaTitle/{details.get('imagelogo', f'{manhwa_name}.webp')}",
        "updateChap": f"backend/updateChap/update_{manhwa_name}.webp",
        "sideImage": f"backend/sideImage/{details.get('sideImage', f'{manhwa_name}.webp')}",
        "synopsis": details.get("synopsis", ""),
        "artist": details.get("artist", ""),
        "author": details.get("author", ""),
        "genres": details.get("genres", []),
        "keywords": details.get("keywords", []),
        "chaptersAmount": chapters_amount,
        "name": manhwa_name.replace("-", " "),
        "uploadTime": []
    }

    # === Process chapters ===
    for chapter_folder in chapter_folders:
        chapter_path = os.path.join(manhwa_path, chapter_folder)
        if not os.path.isdir(chapter_path):
            continue

        image_files = sorted([
            f for f in os.listdir(chapter_path)
            if f.lower().endswith(('.webp', '.jpg', '.jpeg', '.png'))
        ])
        stat = os.stat(chapter_path)
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        time_str = mod_time.strftime("%H:%M %d/%m/%Y")

        description["uploadTime"].append({
            "chapter": int(chapter_folder.replace("chapter-", "")),
            "time": time_str
        })

        chapter_data = {
            "time": time_str,
            "images": [
                f"/backend/pictures/{manhwa_name}/{chapter_folder}/{img}" for img in image_files
            ]
        }

        chapter_json_path = os.path.join(manhwa_output_dir, f"{chapter_folder}.json")
        with open(chapter_json_path, "w", encoding="utf-8") as f:
            json.dump(chapter_data, f, indent=2)
        print(f"📝 Wrote: {chapter_json_path}")

    # === Save description after processing all chapters ===
    description_path = os.path.join(manhwa_output_dir, "manwhaDescription.json")
    with open(description_path, "w", encoding="utf-8") as f:
        json.dump(description, f, indent=2)
    print(f"✅ Updated: {description_path}")
