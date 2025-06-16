import os
import json
import requests
from bs4 import BeautifulSoup

# === PATHS ===
json_path = os.path.expanduser("~/server-backend/json/manhwa_list.json")
details_path = os.path.expanduser("~/server-backend/json/manwha_details.json")
image_dir = os.path.expanduser("~/backend/manwhaTitle")

# === LOAD ===
with open(json_path, "r", encoding="utf-8") as f:
    manhwa_list = json.load(f)

if os.path.exists(details_path):
    with open(details_path, "r", encoding="utf-8") as f:
        manwha_details = json.load(f)
else:
    manwha_details = {}

headers = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()

found_any = False

# === SCRAPE ===
for slug, sources in manhwa_list.items():
    site_entry = next((s for s in sources if s.get("site") == "manhwaclan"), None)
    if not site_entry:
        print(f"↪️ Skipping {slug}: no manhwaclan source")
        continue

    found_any = True
    url = f"https://manhwaclan.com/manga/{slug.replace('_', '-')}/"
    print(f"🔎 Checking {slug} (manhwaclan)")

    try:
        res = session.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(res.text, "html.parser")

        current = manwha_details.get(slug, {})

        # === Ensure default fields
        current.setdefault("synopsis", "")
        current.setdefault("artist", "")
        current.setdefault("author", "")
        current.setdefault("keywords", [])
        current.setdefault("genres", [])

        # === IMAGE
        image_name = f"{slug}.webp"
        image_path = os.path.join(image_dir, image_name)
        img_tag = soup.select_one("div.summary_image a img")
        img_src = img_tag["src"].strip() if img_tag else ""

        if "imagelogo" not in current or not os.path.exists(image_path):
            if img_src:
                try:
                    img_data = session.get(img_src, headers=headers, timeout=30).content
                    with open(image_path, "wb") as img_file:
                        img_file.write(img_data)
                    print(f"✅ Image saved: {image_name}")
                    current["imagelogo"] = image_name
                except Exception as img_err:
                    print(f"⚠️ Failed to download image for {slug}: {img_err}")
        else:
            print(f"↪️ Image already exists: {image_name}")

        # === SYNOPSIS
        if not current["synopsis"].strip():
            syn_tag = soup.select_one("div.summary__content p")
            if syn_tag:
                current["synopsis"] = syn_tag.text.strip()

        # === KEYWORDS (Alternative)
        if not current["keywords"]:
            for block in soup.select("div.post-content_item"):
                heading = block.select_one("div.summary-heading")
                if heading and heading.text.strip() == "Alternative":
                    content = block.select_one("div.summary-content")
                    if content:
                        raw_text = content.text.strip()
                        current["keywords"] = [kw.strip() for kw in raw_text.split(",") if kw.strip()]
                    break

        # === GENRES
        if not current["genres"]:
            for block in soup.select("div.post-content_item"):
                heading = block.select_one("div.summary-heading")
                if heading and heading.text.strip() == "Genre(s)":
                    genre_links = block.select("div.summary-content div.genres-content a")
                    current["genres"] = [a.text.strip() for a in genre_links if a.text.strip()]
                    break

        # === AUTHOR / ARTIST
        for block in soup.select("div.post-content_item"):
            heading = block.select_one("div.summary-heading")
            label = heading.text.strip() if heading else ""
            content = block.select_one("div.summary-content")
            value = content.text.strip() if content else ""

            if label == "Author(s)" and (not current["author"] or current["author"] == "--"):
                current["author"] = value
            elif label == "Artist(s)" and (not current["artist"] or current["artist"] == "--"):
                current["artist"] = value

        # === Save back
        manwha_details[slug] = current

    except Exception as e:
        print(f"❌ Error processing {slug}: {e}")

# === SAVE
with open(details_path, "w", encoding="utf-8") as f:
    json.dump(manwha_details, f, indent=2)

if not found_any:
    print("⚠️ No manhwaclan entries found in manhwa_list.json")
