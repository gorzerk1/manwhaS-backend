import os
import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone as dt_timezone
from pytz import timezone

# === LOAD MANHWA LIST FROM JSON ===
with open("/home/ubuntu/server-backend/json/manhwa_list.json", "r") as f:
    manhwa_list = json.load(f)

# === PATHS ===
pictures_path = os.path.expanduser("~/backend/pictures")
log_dir = os.path.expanduser("~/backend/logs/searchNewChapters")

# === GET LATEST LOCAL CHAPTER ===
def get_local_latest_chapter(folder_path):
    chapter_nums = []
    for name in os.listdir(folder_path):
        match = re.match(r"chapter-(\d+)", name.lower())
        if match:
            chapter_nums.append(int(match.group(1)))
    return max(chapter_nums) if chapter_nums else None

# === CHECK ONLINE CHAPTER ===
def check_online_chapter(name, data):
    site = data.get("site")
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        if site == "asura":
            url = f"https://asuracomic.net/series/{name}-{data['id']}"
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select("a[href*='/chapter/']")
            chapter_nums = [int(m.group(1)) for link in links if (m := re.search(r'/chapter/(\d{1,4})', link.get("href", "")))]
            return max(chapter_nums) if chapter_nums else None

        elif site == "yaksha":
            url = f"https://yakshascans.com/manga/{name}"
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select("li.wp-manga-chapter a[href*='/chapter-']")
            chapter_nums = [int(m.group(1)) for link in links if (m := re.search(r'/chapter-(\d{1,4})', link.get("href", "")))]
            return max(chapter_nums) if chapter_nums else None

        elif site == "kunmanga":
            url = f"https://kunmanga.com/manga/{name}/"
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select("li.wp-manga-chapter a[href*='/chapter-']")
            chapter_nums = [int(m.group(1)) for link in links if (m := re.search(r'chapter-(\d{1,4})', link.get("href", "")))]
            return max(chapter_nums) if chapter_nums else None

        elif site == "manhwaclan":
            url = f"https://manhwaclan.com/manga/{name}/"
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select("div.listing-chapters_wrap a[href*='/chapter-']")
            chapter_nums = [int(m.group(1)) for link in links if (m := re.search(r'/chapter-(\d+)', link.get("href", "")))]
            return max(chapter_nums) if chapter_nums else None

        elif site == "manhuaplus":
            url = f"https://manhuaplus.org/manga/{name}/"
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.select("ul#myUL li[data]")
            chapter_nums = []
            for item in items:
                data_val = item.get("data", "")
                match = re.search(r'chapter[^0-9]*?(\d{1,4})', data_val, re.IGNORECASE)
                if match:
                    chapter_nums.append(int(match.group(1)))
            return max(chapter_nums) if chapter_nums else None

        elif site == "readkingdom":
            url = "https://ww4.readkingdom.com"
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select("a[href*='/chapter/kingdom-chapter-']")
            chapter_nums = [int(m.group(1)) for link in links if (m := re.search(r'kingdom-chapter-(\d{1,4})', link.get("href", "")))]
            return max(chapter_nums) if chapter_nums else None

    except Exception as e:
        print(f"❌ Error for {name} ({site}): {e}")
        return None

    return None

# === LOG NEW CHAPTER ===
def log_new_chapter(name, site, local, online):
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "new_chapters.log")
    with open(log_path, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {site} - {name}: Local {local} → Online {online}\n")

# === LOG NO NEW ===
def log_no_new_chapters():
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "new_chapters.log")
    ec2_time = datetime.now(dt_timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    israel_time = datetime.now(timezone("Israel")).strftime("%Y-%m-%d %H:%M:%S")
    message = f"No new chapters found - {ec2_time} ({israel_time} of GMT+3)"
    print(message)
    with open(log_path, "a") as f:
        f.write(message + "\n")

# === MAIN ===
if __name__ == "__main__":
    new_found = False
    for folder in sorted(os.listdir(pictures_path)):
        folder_path = os.path.join(pictures_path, folder)
        if os.path.isdir(folder_path) and folder in manhwa_list:
            local_chapter = get_local_latest_chapter(folder_path)
            entries = manhwa_list[folder]

            for data in entries:
                site = data.get("site", "unknown")
                online_chapter = check_online_chapter(folder, data)

                if online_chapter is not None and (not local_chapter or online_chapter > local_chapter):
                    print(f"🆕 {site} - {folder}: New Chapter {online_chapter}")
                    log_new_chapter(folder, site, local_chapter, online_chapter)
                    new_found = True
                    break
                else:
                    online_str = "❌ error" if online_chapter is None else online_chapter
                    print(f"✅ {site} - {folder}: No new chapter (Local: {local_chapter}, Online: {online_str})")

    if not new_found:
        log_no_new_chapters()
