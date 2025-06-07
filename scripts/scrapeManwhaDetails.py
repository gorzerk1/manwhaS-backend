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
    print(f"🔎 Scraping {slug} from {url}")

    try:
        res = session.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(res.text, "html.parser")

        # image
        img_tag = soup.select_one("img.rounded.mx-auto.md\\:mx-0")
        img_src = img_tag["src"].strip() if img_tag else ""
        image_name = f"{slug}.webp"
        image_path = os.path.join(image_dir, image_name)

        if not os.path.exists(image_path) and img_src:
            try:
                img_data = session.get(img_src, headers=headers, timeout=30).content
                with open(image_path, "wb") as img_file:
                    img_file.write(img_data)
                print(f"✅ Downloaded image: {image_name}")
            except Exception as img_err:
                print(f"⚠️ Failed to download image for {slug}: {img_err}")
        else:
            print(f"↪️ Using existing image: {image_name}")

        # synopsis
        syn_tag = soup.select_one("span.font-medium.text-sm.text-\\[\\#A2A2A2\\]")
        synopsis = syn_tag.text.strip() if syn_tag else ""

        # genres from buttons
        genre_block = soup.select_one("div.flex.flex-row.flex-wrap.gap-3")
        genres = [btn.text.strip() for btn in genre_block.find_all("button")] if genre_block else []

        # keywords from span
        keyword_tags = soup.select("span.text-\\[\\#A2A2A2\\].font-normal")
        keywords = list({k.text.strip() for k in keyword_tags})

        # artist and author
        artist = get_detail_from_block(soup, "Artist")
        author = get_detail_from_block(soup, "Author")

        # save
        manwha_details[slug] = {
            "imagelogo": image_name,
            "synopsis": synopsis,
            "artist": artist,
            "author": author,
            "genres": genres,
            "keywords": keywords
        }

    except Exception as e:
        print(f"❌ Error scraping {slug}: {e}")

# === SAVE ===
with open(details_path, "w", encoding="utf-8") as f:
    json.dump(manwha_details, f, indent=2)
