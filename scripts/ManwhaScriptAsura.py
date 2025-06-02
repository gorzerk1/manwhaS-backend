import os
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep, time
from datetime import datetime
import shutil

# Kill zombie Chrome processes before starting
os.system("pkill -f chrome")
os.system("pkill -f chromedriver")
os.system("pkill -f chromium")
os.system("pkill -f HeadlessChrome")
os.system("pkill -f selenium")

# === Load only 'asura' entries from JSON ===
json_path = os.path.expanduser("~/server-backend/json/manhwa_list.json")
with open(json_path, "r") as f:
    full_data = json.load(f)

manhwa_list = []
for name, sources in full_data.items():
    for entry in sources:
        if entry.get("site") == "asura":
            manhwa_list.append(name)

base_dir = os.path.expanduser("~/backend")
pictures_base = os.path.join(base_dir, "pictures")
log_base = os.path.join(base_dir, "logs")
check_url = "https://asuracomic.net"

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
log_folder = os.path.join(log_base, timestamp)
os.makedirs(log_folder, exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument('--user-agent=Mozilla/5.0')

def start_browser():
    return webdriver.Chrome(options=chrome_options)

def wait_for_connection():
    while True:
        try:
            res = requests.get(check_url, timeout=10)
            if res.status_code == 200:
                print("✅ Website is reachable.")
                return
        except:
            print("❌ Can't connect. Retrying in 5 min...")
        sleep(300)

def get_latest_chapter(name):
    try:
        url = f"https://asuracomic.net/manga/{name}/"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        chapter_links = soup.select("a[href*='/chapter/']")
        chapter_numbers = []
        for link in chapter_links:
            href = link.get("href", "")
            try:
                num = int(href.split("/chapter/")[1].split("/")[0])
                chapter_numbers.append(num)
            except:
                continue
        return max(chapter_numbers) if chapter_numbers else 1
    except Exception as e:
        print(f"❌ Failed to get latest chapter: {e}")
        return 1

start_time = time()
wait_for_connection()
all_errors = []

for name in manhwa_list:
    series_url = f"https://asuracomic.net/manga/{name}/chapter/{{}}"
    manhwa_dir = os.path.join(pictures_base, name)
    log_file_path = os.path.join(log_folder, f"{name}.txt")
    log_lines = []

    print(f"\n📚 Processing manhwa: {name}")
    os.makedirs(manhwa_dir, exist_ok=True)
    chapter_end = get_latest_chapter(name)

    for chapter in range(1, chapter_end + 1):
        chapter_dir = os.path.join(manhwa_dir, f"chapter-{chapter}")
        chapter_url = series_url.format(chapter)

        if os.path.exists(chapter_dir):
            source_file = os.path.join(chapter_dir, "source.txt")
            if os.path.exists(source_file):
                with open(source_file, "r") as f:
                    tag = f.read().strip()
                if tag != "Downloaded from AsuraScans":
                    print(f"🗑️ Chapter {chapter} not from Asura → Re-downloading...")
                    shutil.rmtree(chapter_dir, ignore_errors=True)
                else:
                    log_lines.append(f"[Chapter {chapter}] Skipped (already from AsuraScans)")
                    continue
            else:
                log_lines.append(f"[Chapter {chapter}] Skipped (no source file, assuming Asura)")
                continue

        print(f"📅 Downloading Chapter {chapter}...")
        success = False
        for attempt in range(1, 6):
            driver = None
            try:
                driver = start_browser()
                driver.set_page_load_timeout(60)
                driver.get(chapter_url)

                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "img.object-cover.mx-auto"))
                    )
                    img_elements = driver.find_elements(By.CSS_SELECTOR, "img.object-cover.mx-auto")
                except:
                    img_elements = []

                if not img_elements:
                    raise Exception("No images found")

                os.makedirs(chapter_dir, exist_ok=True)
                for i, img in enumerate(img_elements):
                    img_url = img.get_attribute("src")
                    ext = img_url.split(".")[-1].split("?")[0]
                    img_name = f"{i+1:03d}.{ext}"
                    img_path = os.path.join(chapter_dir, img_name)
                    img_data = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).content
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    sleep(0.3)

                with open(os.path.join(chapter_dir, "source.txt"), "w") as f:
                    f.write("Downloaded from AsuraScans")

                print(f"✅ Saved chapter {chapter}")
                log_lines.append(f"[Chapter {chapter}] ✅ Done")
                success = True
                break

            except Exception as e:
                print(f"❌ Attempt {attempt}/5 failed: {e}")
                sleep(3)

            finally:
                if driver:
                    try: driver.quit()
                    except: pass

        if not success:
            log_lines.append(f"[Chapter {chapter}] ❌ Failed")
            all_errors.append(f"{name} Chapter {chapter}: failed after retries")
            if os.path.exists(chapter_dir):
                print(f"🧹 Removing failed chapter folder: {chapter_dir}")
                shutil.rmtree(chapter_dir, ignore_errors=True)

    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"📚 Log for: {name}\n\n")
        log_file.write("\n".join(log_lines))

    print(f"📝 Log saved for {name} → {log_file_path}")

end_time = time()
print(f"\n⏱️ Finished in {end_time - start_time:.2f} sec")
