import os
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from time import sleep

# Kill zombie Chrome processes
os.system("pkill -f chrome")
os.system("pkill -f chromedriver")
os.system("pkill -f chromium")
os.system("pkill -f HeadlessChrome")
os.system("pkill -f selenium")

# === PATHS ===
base_dir = os.path.expanduser("~/backend")
pictures_base = os.path.join(base_dir, "pictures")
json_path = os.path.expanduser("~/server-backend/json/manhwa_list.json")

# === CHROME SETUP ===
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument('--user-agent=Mozilla/5.0')

def start_browser():
    return webdriver.Chrome(options=chrome_options)

# === JSON LOAD ===
with open(json_path, "r", encoding="utf-8") as f:
    manhwa_data = json.load(f)

# === SITE SETTINGS ===
SITE_CONFIG = {
    "yaksha": {
        "url": "https://yakshascans.com/manga/{slug}/chapter-{chapter}/",
        "selector": "div.page-break.no-gaps img",
        "attr": "src",
        "sleep": 8
    },
    "manhwaclan": {
        "url": "https://manhwaclan.com/manga/{slug}/chapter-{chapter}/",
        "selector": "div.page-break.no-gaps img",
        "attr": "src",
        "sleep": 5
    },
    "manhuaus": {
        "url": "https://manhuaus.com/manga/{slug}/chapter-{chapter}",
        "selector": "div.page-break.no-gaps img",
        "attr": "data-src",
        "sleep": 5
    },
    "kunmanga": {
        "custom": True
    }
}

# === FUNCTIONS ===
def download_kunmanga_chapter(slug, chapter_num, local_path):
    try:
        url = f"https://kunmanga.com/manga/{slug}/chapter-{chapter_num}/"
        chapter_dir = os.path.join(local_path, f"chapter-{chapter_num}")
        print(f"\n🔎 Checking kunmanga: {slug} Chapter {chapter_num}")

        driver.get(url)
        sleep(2)

        imgs = driver.find_elements(By.CSS_SELECTOR, "div.reading-content div.page-break img")
        img_urls = [img.get_attribute("src") for img in imgs if img.get_attribute("src")]

        if len(img_urls) <= 1:
            print(f"✅ No real chapter content for {slug} chapter {chapter_num}")
            return False

        os.makedirs(chapter_dir, exist_ok=True)
        for i, img_url in enumerate(img_urls):
            ext = img_url.split('.')[-1].split('?')[0]
            name = f"{i+1:03d}.{ext}"
            path = os.path.join(chapter_dir, name)
            res = session.get(img_url, headers=headers, timeout=30)
            with open(path, "wb") as f:
                f.write(res.content)
            print(f"✅ Saved {name}")

        with open(os.path.join(chapter_dir, "source.txt"), "w") as f:
            f.write("Downloaded from KunManga")

        return True

    except Exception as e:
        print(f"❌ Error checking kunmanga for {slug}: {e}")
        return False

# === MAIN ===
session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0"}
driver = start_browser()

# === DOWNLOAD LOGIC ===
for slug, sources in manhwa_data.items():
    supported_sources = [s for s in sources if s.get("site") in SITE_CONFIG]
    if not supported_sources:
        continue

    local_path = os.path.join(pictures_base, slug)
    if not os.path.exists(local_path):
        print(f"⚠️ Folder missing for {slug}")
        continue

    local_chapters = [
        int(f.split("-")[-1]) for f in os.listdir(local_path)
        if f.startswith("chapter-") and f.split("-")[-1].isdigit()
    ]
    last_local_chapter = max(local_chapters) if local_chapters else 0

    print(f"\n📘 Now processing: {slug}")
    new_chapter = last_local_chapter + 1

    while True:
        downloaded = False
        for source in supported_sources:
            site = source["site"]
            site_slug = source.get("name", slug)
            config = SITE_CONFIG[site]

            print(f"\n🔎 Trying {site}: {site_slug} Chapter {new_chapter}")

            if config.get("custom"):
                success = download_kunmanga_chapter(site_slug, new_chapter, local_path)
                if success:
                    downloaded = True
                    break
                continue

            try:
                url = config["url"].format(slug=site_slug, chapter=new_chapter)
                driver.get(url)
                sleep(config["sleep"])

                imgs = driver.find_elements(By.CSS_SELECTOR, config["selector"])
                img_urls = [img.get_attribute(config["attr"]) for img in imgs if img.get_attribute(config["attr"])]

                if len(img_urls) <= 1:
                    print(f"✅ No real chapter content for {site_slug} chapter {new_chapter}")
                    continue

                chapter_dir = os.path.join(local_path, f"chapter-{new_chapter}")
                os.makedirs(chapter_dir, exist_ok=True)
                for i, img_url in enumerate(img_urls):
                    ext = img_url.split('.')[-1].split('?')[0]
                    name = f"{i+1:03d}.{ext}"
                    path = os.path.join(chapter_dir, name)
                    res = session.get(img_url, headers=headers, timeout=30)
                    with open(path, "wb") as f:
                        f.write(res.content)
                    print(f"✅ Saved {name}")

                with open(os.path.join(chapter_dir, "source.txt"), "w") as f:
                    f.write(f"Downloaded from {site}")

                downloaded = True
                break

            except Exception as e:
                print(f"❌ Error checking {site} for {site_slug}: {e}")
                continue

        if not downloaded:
            print(f"⚠️ Chapter {new_chapter} not found on any source for {slug}")
            break 
        else:
            new_chapter += 1

driver.quit()
