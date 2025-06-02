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

# Kill zombie Chrome processes
os.system("pkill -f chrome")
os.system("pkill -f chromedriver")
os.system("pkill -f chromium")
os.system("pkill -f HeadlessChrome")
os.system("pkill -f selenium")

# === CONFIG ===
json_path = os.path.expanduser("~/server-backend/json/manhwa_list.json")
base_dir = os.path.expanduser("~/backend")
pictures_base = os.path.join(base_dir, "pictures")
log_base = os.path.join(base_dir, "logs")
check_url = "https://asuracomic.net"

# === FIND ID ===
def fetch_asura_id(slug):
    try:
        url = f"https://asuracomic.net/?s={slug.replace('-', '+')}"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.select("a[href*='/series/']"):
            href = link.get("href", "")
            if f"/series/{slug}-" in href:
                return href.split(f"/series/{slug}-")[1].split("/")[0]
    except: return None

# === LOAD LIST ===
with open(json_path, "r") as f:
    full_data = json.load(f)

manhwa_list = []
for name, sources in full_data.items():
    for entry in sources:
        if entry.get("site") == "asura":
            series_id = entry.get("id") or fetch_asura_id(name)
            if series_id:
                manhwa_list.append({"name": name, "id": series_id})

# === SETUP ===
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

def get_latest_chapter(slug_id):
    try:
        url = f"https://asuracomic.net/series/{slug_id}"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.select("a[href*='/chapter/']")
        nums = []
        for link in links:
            href = link.get("href", "")
            try:
                nums.append(int(href.split("/chapter/")[1].split("/")[0]))
            except: continue
        return max(nums) if nums else 1
    except Exception as e:
        print(f"❌ get_latest_chapter error: {e}")
        return 1

# === MAIN ===
start_time = time()
wait_for_connection()
all_errors = []

for manhwa in manhwa_list:
    name = manhwa["name"]
    id_ = manhwa["id"]
    slug_id = f"{name}-{id_}"
    url_format = f"https://asuracomic.net/series/{slug_id}/chapter/{{}}"
    folder_path = os.path.join(pictures_base, name)
    log_path = os.path.join(log_folder, f"{name}.txt")
    log_lines = []

    print(f"\n📚 Processing manhwa: {name}")
    os.makedirs(folder_path, exist_ok=True)
    last_chapter = get_latest_chapter(slug_id)

    for chap in range(1, last_chapter + 1):
        chap_folder = os.path.join(folder_path, f"chapter-{chap}")
        chap_url = url_format.format(chap)

        if os.path.exists(chap_folder):
            src_file = os.path.join(chap_folder, "source.txt")
            if os.path.exists(src_file):
                with open(src_file) as f:
                    if f.read().strip() == "Downloaded from AsuraScans":
                        log_lines.append(f"[Chapter {chap}] Skipped (already from AsuraScans)")
                        continue
                print(f"🗑️ Chapter {chap} not from Asura → Re-downloading...")
                shutil.rmtree(chap_folder, ignore_errors=True)
            else:
                log_lines.append(f"[Chapter {chap}] Skipped (no source file, assuming Asura)")
                continue

        print(f"📅 Downloading Chapter {chap}...")
        success = False
        for attempt in range(1, 6):
            driver = None
            try:
                driver = start_browser()
                driver.set_page_load_timeout(60)
                driver.get(chap_url)

                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img.object-cover.mx-auto"))
                )
                images = driver.find_elements(By.CSS_SELECTOR, "img.object-cover.mx-auto")

                if not images:
                    raise Exception("No images found")

                os.makedirs(chap_folder, exist_ok=True)
                for i, img in enumerate(images):
                    src = img.get_attribute("src")
                    ext = src.split(".")[-1].split("?")[0]
                    file_name = f"{i+1:03d}.{ext}"
                    img_data = requests.get(src, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).content
                    with open(os.path.join(chap_folder, file_name), "wb") as f:
                        f.write(img_data)
                    sleep(0.3)

                with open(os.path.join(chap_folder, "source.txt"), "w") as f:
                    f.write("Downloaded from AsuraScans")

                print(f"✅ Saved chapter {chap}")
                log_lines.append(f"[Chapter {chap}] ✅ Done")
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
            log_lines.append(f"[Chapter {chap}] ❌ Failed")
            all_errors.append(f"{name} Chapter {chap}: failed after retries")
            if os.path.exists(chap_folder):
                print(f"🧹 Removing failed chapter folder: {chap_folder}")
                shutil.rmtree(chap_folder, ignore_errors=True)

    with open(log_path, "w", encoding="utf-8") as logf:
        logf.write(f"📚 Log for: {name}\n\n")
        logf.write("\n".join(log_lines))

    print(f"📝 Log saved for {name} → {log_path}")

print(f"\n⏱️ Finished in {time() - start_time:.2f} sec")
