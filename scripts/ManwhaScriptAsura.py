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

# ---------- Kill zombie Chrome -------------------------------------------
os.system("pkill -f chrome")
os.system("pkill -f chromedriver")
os.system("pkill -f chromium")
os.system("pkill -f HeadlessChrome")
os.system("pkill -f selenium")

# ---------- CONFIG --------------------------------------------------------
SCRIPT_NAME   = "ManwhaScriptAsura"
LOG_FILENAME  = "new_chapters.log"

json_path     = os.path.expanduser("~/server-backend/json/manhwa_list.json")
base_dir      = os.path.expanduser("~/backend")
pictures_base = os.path.join(base_dir, "pictures")
log_base      = os.path.join(base_dir, "logs")

# Folder for this script
log_dir       = os.path.join(log_base, SCRIPT_NAME)
os.makedirs(log_dir, exist_ok=True)

log_path      = os.path.join(log_dir, LOG_FILENAME)

check_url     = "https://asuracomic.net"

# ---------- Single line‑buffered log file ---------------------------------
# buffering=1  --> line buffered → every .write() flushes immediately
log_handle = open(log_path, "a", encoding="utf-8", buffering=1)

def log(msg: str) -> None:
    """Print to console *and* append the message to the single log file."""
    print(msg)
    log_handle.write(f"{msg}\n")

# ---------- Load manhwa list ---------------------------------------------
with open(json_path, "r") as f:
    full_data = json.load(f)

manhwa_list = []
for name, sources in full_data.items():
    for entry in sources:
        if entry.get("site") == "asura":
            url = entry.get("url")
            if isinstance(url, str) and url.startswith("https://asuracomic.net/series/"):
                manhwa_list.append({"name": name, "url": url})
            else:
                print(f"⚠️  Missing or invalid URL for: {name}")

# ---------- Selenium options ---------------------------------------------
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--user-agent=Mozilla/5.0")

def start_browser():
    return webdriver.Chrome(options=chrome_options)

# ---------- Helpers -------------------------------------------------------
def wait_for_connection():
    """Block until the target site is reachable."""
    while True:
        try:
            res = requests.get(check_url, timeout=10)
            if res.status_code == 200:
                print("✅ Website is reachable.")
                return
        except Exception:
            print("❌ Can't connect. Retrying in 5 min...")
        sleep(300)

def get_latest_chapter(base_url: str) -> int:
    """Return the highest chapter number found on the series page."""
    try:
        res = requests.get(base_url,
                           headers={"User-Agent": "Mozilla/5.0"},
                           timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.select("a[href*='/chapter/']")
        nums = []
        for link in links:
            href = link.get("href", "")
            try:
                nums.append(int(href.split("/chapter/")[1].split("/")[0]))
            except (ValueError, IndexError):
                continue
        return max(nums) if nums else 1
    except Exception as e:
        print(f"❌ get_latest_chapter error: {e}")
        return 1

# =======================================================================
# MAIN
# =======================================================================
start_time = time()
wait_for_connection()

for manhwa in manhwa_list:
    name      = manhwa["name"]
    base_url  = manhwa["url"]
    url_format = f"{base_url}/chapter/{{}}"

    folder_path = os.path.join(pictures_base, name)
    os.makedirs(folder_path, exist_ok=True)

    print(f"\n📚 Processing manhwa: {name}")
    last_chapter = get_latest_chapter(base_url)

    # -------------------------------------------------------------------
    for chap in range(1, last_chapter + 1):
        chap_folder  = os.path.join(folder_path, f"chapter-{chap}")
        temp_folder  = os.path.join(folder_path, f"chapter-{chap}_temp")
        chap_url     = url_format.format(chap)
        needs_replacement = False

        # --------- Skip chapters that are already downloaded ------------
        if os.path.exists(chap_folder):
            src_file = os.path.join(chap_folder, "source.txt")
            if os.path.exists(src_file):
                with open(src_file) as f:
                    if f.read().strip() == "Downloaded from AsuraScans":
                        # Already downloaded by our script; nothing to log
                        continue
                    else:
                        needs_replacement = True
            else:
                # Old folder without source.txt; treat as "unknown", skip
                continue

        # --------- Download (only if we need it) ------------------------
        driver = None
        try:
            driver = start_browser()
            driver.set_page_load_timeout(60)
            driver.set_script_timeout(30)

            driver.get(chap_url)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "img.object-cover.mx-auto"))
            )
            images = driver.find_elements(
                By.CSS_SELECTOR, "img.object-cover.mx-auto")

            if not images:
                raise Exception("No images found")

            os.makedirs(temp_folder, exist_ok=True)
            for i, img in enumerate(images):
                src = WebDriverWait(driver, 10).until(
                    lambda d: img.get_attribute("src"))
                ext = src.split(".")[-1].split("?")[0]
                file_name = f"{i+1:03d}.{ext}"
                img_data = requests.get(
                    src,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10
                ).content
                with open(os.path.join(temp_folder, file_name), "wb") as f:
                    f.write(img_data)
                sleep(0.3)  # polite pause

            # Mark folder as ours
            with open(os.path.join(temp_folder, "source.txt"), "w") as f:
                f.write("Downloaded from AsuraScans")

            # Replace old folder if needed
            if needs_replacement:
                shutil.rmtree(chap_folder, ignore_errors=True)

            os.rename(temp_folder, chap_folder)

            # -------- SUCCESS → write one concise log line --------------
            log(f"✅ Downloaded {name} chapter {chap}")

        except Exception as e:
            shutil.rmtree(temp_folder, ignore_errors=True)
            log(f"❌ {name} chapter {chap} – {e}")

        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

# ---------- Clean up ------------------------------------------------------
log_handle.close()
print(f"\n⏱️ Finished in {time() - start_time:.2f} sec")
