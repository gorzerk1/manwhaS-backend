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

# === HELPER ===
def get_detail_from_block(soup, label):
    block = soup.find("h3", string=label)
    if not block:
        return "--"
    parent = block.find_parent("div")
    if not parent:
        return "--"
    values = parent.find_all("h3")
    return values[1].text.strip() if len(values) > 1 else "--"

# === SCRAPE ===
for slug, sources in manhwa_list.items():
    asura = next((s for s in sources if s.get("site") == "asura" and "url" in s), None)
    if not asura:
        continue

    url = asura["url"]
    print(f"🔎 Checking {slug}")

    try:
        res = session.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(res.text, "html.parser")

        current = manwha_details.get(slug, {})

        # === IMAGE
        image_name = f"{slug}.webp"
        image_path = os.path.join(image_dir, image_name)
        img_tag = soup.select_one("img.rounded.mx-auto.md\\:mx-0")
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
        if "synopsis" not in current or not current["synopsis"].strip():
            syn_tag = soup.select_one("span.font-medium.text-sm.text-\\[\\#A2A2A2\\]")
            if syn_tag:
                current["synopsis"] = syn_tag.text.strip()

        # === GENRES
        if "genres" not in current or not current["genres"]:
            genre_block = soup.select_one("div.flex.flex-row.flex-wrap.gap-3")
            if genre_block:
                current["genres"] = [btn.text.strip() for btn in genre_block.find_all("button")]

        # === KEYWORDS
        if "keywords" not in current or not current["keywords"]:
            keyword_tags = soup.select("span.text-\\[\\#A2A2A2\\].font-normal")
            current["keywords"] = list({k.text.strip() for k in keyword_tags})

        # === ARTIST
        if "artist" not in current or current["artist"] in ["", "--", "_"]:
            current["artist"] = get_detail_from_block(soup, "Artist")

        # === AUTHOR
        if "author" not in current or current["author"] in ["", "--", "_"]:
            current["author"] = get_detail_from_block(soup, "Author")

        # === Save back to dict
        manwha_details[slug] = current

    except Exception as e:
        print(f"❌ Error processing {slug}: {e}")

# === SAVE
with open(details_path, "w", encoding="utf-8") as f:
    json.dump(manwha_details, f, indent=2)
