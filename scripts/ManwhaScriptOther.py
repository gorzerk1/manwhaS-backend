import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from time import sleep

os.system("pkill -f chrome")
os.system("pkill -f chromedriver")
os.system("pkill -f chromium")
os.system("pkill -f HeadlessChrome")
os.system("pkill -f selenium")


# === PATHS ===
base_dir = os.path.expanduser("~/backend")
pictures_base = os.path.join(base_dir, "pictures")

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

# === MANHUAUS FUNCTION ===
def get_latest_manhuaus_chapter(slug):
    try:
        url = f"https://manhuaus.com/manga/{slug}"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.select(f'a[href*="/manga/{slug}/chapter-"]')
        chapter_numbers = []
        for link in links:
            href = link.get("href", "")
            try:
                num = int(href.split("/chapter-")[1].split("/")[0])
                chapter_numbers.append(num)
            except:
                continue
        return max(chapter_numbers) if chapter_numbers else 0
    except Exception as e:
        print(f"❌ Failed to get manhuaus chapter list for {slug}: {e}")
        return 0

# === KUNMANGA FUNCTION ===
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

# === MANHUAUS ===
manhuaus_list = ["myst-might-mayhem", "absolute-regression"]
for slug in manhuaus_list:
    local_path = os.path.join(pictures_base, slug)
    if not os.path.exists(local_path):
        print(f"❌ Folder missing for {slug}")
        continue

    local_chapters = [
        int(f.split("-")[-1]) for f in os.listdir(local_path)
        if f.startswith("chapter-") and f.split("-")[-1].isdigit()
    ]
    last_local_chapter = max(local_chapters) if local_chapters else 0
    latest_online_chapter = get_latest_manhuaus_chapter(slug)

    if latest_online_chapter <= last_local_chapter:
        print(f"✅ No new chapter for {slug} (Local: {last_local_chapter}, Online: {latest_online_chapter})")
        continue

    for new_chapter in range(last_local_chapter + 1, latest_online_chapter + 1):
        url = f"https://manhuaus.com/manga/{slug}/chapter-{new_chapter}"
        chapter_dir = os.path.join(local_path, f"chapter-{new_chapter}")
        print(f"\n🔎 Checking manhuaus: {slug} Chapter {new_chapter}")
        try:
            driver.get(url)
            sleep(2)

            if driver.current_url.rstrip("/") == f"https://manhuaus.com/manga/{slug}":
                print(f"✅ No new chapter for {slug} (redirected)")
                break

            imgs = driver.find_elements(By.CSS_SELECTOR, "div.page-break.no-gaps img")
            img_urls = [img.get_attribute("data-src") for img in imgs if img.get_attribute("data-src")]

            if len(img_urls) <= 1:
                print(f"✅ No real chapter content for {slug} chapter {new_chapter}")
                break

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
                f.write("Downloaded from Manhuaus")

        except Exception as e:
            print(f"❌ Error checking manhuaus for {slug}: {e}")
            break

# === YAKSHA ===
yaksha_list = ["myst-might-mayhem", "the-return-of-the-crazy-demon"]
for slug in yaksha_list:
    local_path = os.path.join(pictures_base, slug)
    if not os.path.exists(local_path):
        print(f"❌ Folder missing for {slug}")
        continue

    local_chapters = [
        int(f.split("-")[-1]) for f in os.listdir(local_path)
        if f.startswith("chapter-") and f.split("-")[-1].isdigit()
    ]
    last_local_chapter = max(local_chapters) if local_chapters else 0

    for new_chapter in range(last_local_chapter + 1, last_local_chapter + 6):
        url = f"https://yakshascans.com/manga/{slug}/chapter-{new_chapter}/"
        chapter_dir = os.path.join(local_path, f"chapter-{new_chapter}")
        print(f"\n🔎 Checking yakshascans: {slug} Chapter {new_chapter}")
        try:
            driver.get(url)
            sleep(8)

            if driver.current_url.rstrip("/") == f"https://yakshascans.com/manga/{slug}":
                print(f"✅ No new chapter for {slug} (redirected)")
                break

            imgs = driver.find_elements(By.CSS_SELECTOR, "div.page-break.no-gaps img")
            img_urls = [img.get_attribute("src") for img in imgs if img.get_attribute("src")]

            if len(img_urls) <= 1:
                print(f"✅ No real chapter content for {slug} chapter {new_chapter}")
                break

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
                f.write("Downloaded from YakshaScans")

        except Exception as e:
            print(f"❌ Error checking yakshascans for {slug}: {e}")
            break

# === KUNMANGA ===
kunmanga_list = ["absolute-regression", "myst-might-mayhem"]
for slug in kunmanga_list:
    local_path = os.path.join(pictures_base, slug)
    if not os.path.exists(local_path):
        print(f"❌ Folder missing for {slug}")
        continue

    local_chapters = [
        int(f.split("-")[-1]) for f in os.listdir(local_path)
        if f.startswith("chapter-") and f.split("-")[-1].isdigit()
    ]
    last_local_chapter = max(local_chapters) if local_chapters else 0

    for new_chapter in range(last_local_chapter + 1, last_local_chapter + 6):
        success = download_kunmanga_chapter(slug, new_chapter, local_path)
        if not success:
            break


# === MANHWACLAN ===
manhwaclan_list = ["surviving-as-a-genius-on-borrowed-time", "myst-might-mayhem"]
for slug in manhwaclan_list:
    local_path = os.path.join(pictures_base, slug)
    if not os.path.exists(local_path):
        print(f"❌ Folder missing for {slug}")
        continue

    local_chapters = [
        int(f.split("-")[-1]) for f in os.listdir(local_path)
        if f.startswith("chapter-") and f.split("-")[-1].isdigit()
    ]
    last_local_chapter = max(local_chapters) if local_chapters else 0

    for new_chapter in range(last_local_chapter + 1, last_local_chapter + 6):
        url = f"https://manhwaclan.com/manga/{slug}/chapter-{new_chapter}/"
        chapter_dir = os.path.join(local_path, f"chapter-{new_chapter}")
        print(f"\n🔎 Checking manhwaclan: {slug} Chapter {new_chapter}")
        try:
            driver.get(url)
            sleep(5)

            if driver.current_url.rstrip("/") == f"https://manhwaclan.com/manga/{slug}":
                print(f"✅ No new chapter for {slug} (redirected)")
                break

            imgs = driver.find_elements(By.CSS_SELECTOR, "div.page-break.no-gaps img")
            img_urls = [img.get_attribute("src") for img in imgs if img.get_attribute("src")]

            if len(img_urls) <= 1:
                print(f"✅ No real chapter content for {slug} chapter {new_chapter}")
                break

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
                f.write("Downloaded from Manhwaclan")

        except Exception as e:
            print(f"❌ Error checking manhwaclan for {slug}: {e}")
            break

driver.quit()
