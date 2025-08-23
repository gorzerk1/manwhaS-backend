#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import uuid
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

os.system("pkill -f chrome")
os.system("pkill -f chromedriver")
os.system("pkill -f chromium")
os.system("pkill -f HeadlessChrome")
os.system("pkill -f selenium")

SCRIPT_NAME   = "ManwhaScriptAsura"
LOG_FILENAME  = "new_chapters.log"

json_path     = os.path.expanduser("~/server-backend/json/manhwa_list.json")
base_dir      = os.path.expanduser("~/backend")
pictures_base = os.path.join(base_dir, "pictures")
log_base      = os.path.join(base_dir, "logs")

log_dir       = os.path.join(log_base, SCRIPT_NAME)
os.makedirs(log_dir, exist_ok=True)

profiles_root = os.path.join(log_dir, "chrome-profiles")
os.makedirs(profiles_root, exist_ok=True)

log_path      = os.path.join(log_dir, LOG_FILENAME)
check_url     = "https://asuracomic.net"

log_handle = open(log_path, "a", encoding="utf-8", buffering=1)

def log(msg: str) -> None:
    print(msg)
    log_handle.write(f"{msg}\n")

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

def start_browser():
    profile_dir = os.path.join(profiles_root, f"profile-{uuid.uuid4().hex}")
    os.makedirs(profile_dir, exist_ok=False)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0")
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--password-store=basic")
    chrome_options.add_argument("--use-mock-keychain")
    chrome_options.add_argument("--remote-debugging-port=0")
    driver = webdriver.Chrome(options=chrome_options)
    driver._profile_dir = profile_dir
    return driver

def wait_for_connection():
    while True:
        try:
            res = requests.get(check_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200:
                print("✅ Website is reachable.")
                return
        except Exception:
            print("❌ Can't connect. Retrying in 5 min...")
        sleep(300)

CHAP_RE = re.compile(r"/chapter/(\d+)(?:[/?#]|$)")

def get_latest_chapter(base_url: str) -> int:
    try:
        res = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        nums = []
        for a in soup.find_all("a", href=True):
            m = CHAP_RE.search(a["href"])
            if m:
                try:
                    nums.append(int(m.group(1)))
                except ValueError:
                    pass
        return max(nums) if nums else 1
    except Exception as e:
        print(f"❌ get_latest_chapter error: {e}")
        return 1

def _gentle_autoscroll(driver, steps=24, pause=0.2):
    last_h = -1
    for _ in range(steps):
        driver.execute_script("window.scrollBy(0, Math.ceil(window.innerHeight*0.9));")
        sleep(pause)
        h = driver.execute_script(
            "return Math.max(document.body.scrollTop, document.documentElement.scrollTop);"
        )
        if h == last_h:
            break
        last_h = h

# --------- collect <img src> inside ALL div.w-full.mx-auto.center ----------
def _collect_image_urls(driver):
    container_sel = "div.w-full.mx-auto.center"

    # Wait until at least one matching <img> is present anywhere on the page
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f"{container_sel} img"))
        )
    except Exception:
        # Fallback: wait for at least one container
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, container_sel))
        )

    # Trigger lazy-loading
    _gentle_autoscroll(driver, steps=30, pause=0.2)

    # Grab ALL <img> elements inside ALL matching containers
    img_elements = driver.find_elements(By.CSS_SELECTOR, f"{container_sel} img")

    urls = []
    seen = set()

    def add(u):
        if not u:
            return
        # strip query/hash for extension check & file naming
        base = u.split("?")[0].split("#")[0]
        ext = base.split(".")[-1].lower() if "." in base else ""
        # accept common raster formats only
        if ext in ("webp", "jpg", "jpeg", "png", "gif"):
            if u not in seen:
                seen.add(u)
                urls.append(u)

    for img in img_elements:
        # Prefer the actual rendered source, then the literal src attribute
        add(img.get_attribute("currentSrc"))
        add(img.get_attribute("src"))

    return urls
# ------------------------------------------------------------------------------

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

    driver = None
    try:
        driver = start_browser()
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(30)

        for chap in range(1, last_chapter + 1):
            chap_folder  = os.path.join(folder_path, f"chapter-{chap}")
            temp_folder  = os.path.join(folder_path, f"chapter-{chap}_temp")
            chap_url     = url_format.format(chap)
            needs_replacement = False

            if os.path.exists(chap_folder):
                src_file = os.path.join(chap_folder, "source.txt")
                if os.path.exists(src_file):
                    with open(src_file) as f:
                        if f.read().strip() == "Downloaded from AsuraScans":
                            continue
                        else:
                            needs_replacement = True
                else:
                    continue

            try:
                driver.get(chap_url)
                image_urls = _collect_image_urls(driver)

                # ===== FIX: skip the first image (cover/banner/ads) =====
                if image_urls:
                    image_urls = image_urls[1:]
                    log(f"ℹ️  Skipped first image for {name} chapter {chap}")

                if not image_urls:
                    raise Exception("No images found after skipping the first image")
                # ========================================================

                os.makedirs(temp_folder, exist_ok=True)
                for i, src in enumerate(image_urls, start=1):
                    # compute extension safely for saving
                    base = src.split("?")[0].split("#")[0]
                    ext = base.split(".")[-1].lower() if "." in base else "jpg"
                    if ext not in ("webp", "jpg", "jpeg", "png", "gif"):
                        ext = "jpg"
                    file_name = f"{i:03d}.{ext}"

                    img_resp = requests.get(
                        src,
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=20
                    )
                    img_resp.raise_for_status()
                    with open(os.path.join(temp_folder, file_name), "wb") as f:
                        f.write(img_resp.content)
                    sleep(0.15)

                with open(os.path.join(temp_folder, "source.txt"), "w") as f:
                    f.write("Downloaded from AsuraScans")

                if needs_replacement:
                    shutil.rmtree(chap_folder, ignore_errors=True)

                os.rename(temp_folder, chap_folder)
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
            try:
                if hasattr(driver, "_profile_dir"):
                    sleep(0.5)
                    shutil.rmtree(driver._profile_dir, ignore_errors=True)
            except Exception:
                pass

log_handle.close()
print(f"\n⏱️ Finished in {time() - start_time:.2f} sec")
