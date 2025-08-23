#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
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
from urllib.parse import urljoin
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

# ---------- Single line-buffered log file ---------------------------------
# buffering=1  --> line buffered → every .write() flushes immediately
log_handle = open(log_path, "a", encoding="utf-8", buffering=1)

def log(msg: str) -> None:
    """Print to console *and* append the message to the single log file."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    log_handle.write(f"{line}\n")

# ---------- Load manhwa list ---------------------------------------------
with open(json_path, "r", encoding="utf-8") as f:
    full_data = json.load(f)

manhwa_list = []
for name, sources in full_data.items():
    for entry in sources:
        if entry.get("site") == "asura":
            url = entry.get("url")
            if isinstance(url, str) and url.startswith("https://asuracomic.net/series/"):
                manhwa_list.append({"name": name, "url": url})
                # helpful debug
                log(f"📄 Loaded series URL for '{name}': {url}")
            else:
                log(f"⚠️  Missing or invalid URL for: {name}")

# ---------- Selenium options ---------------------------------------------
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Chrome 109+ syntax
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--user-agent=Mozilla/5.0")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_prefs = {"profile.managed_default_content_settings.images": 1}
chrome_options.add_experimental_option("prefs", chrome_prefs)

def start_browser():
    return webdriver.Chrome(options=chrome_options)

# ---------- Helpers -------------------------------------------------------
def wait_for_connection():
    """Block until the target site is reachable."""
    while True:
        try:
            log(f"🌐 Probing: {check_url}")
            res = requests.get(check_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            log(f"🌐 Probe HTTP {res.status_code}")
            if res.status_code == 200:
                log("✅ Website is reachable.")
                return
        except Exception as e:
            log(f"❌ Can't connect: {e}. Retrying in 5 min...")
        sleep(300)

# Robust pattern: /chapter/<digits> followed by slash, ?, #, or end
CHAP_RE = re.compile(r"/chapter/(\d+)(?:[/?#]|$)")

def get_latest_chapter(base_url: str) -> int:
    """Return the highest chapter number found on the series page (requests + BS4)."""
    try:
        log(f"🔎 Fetching series page HTML: {base_url}")
        res = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        log(f"🔎 Series HTTP {res.status_code} – received {len(res.text)} bytes")
        # Save a small snapshot for debugging
        snapshot_name = f"{os.path.basename(base_url.rstrip('/'))}_series_snapshot.html"
        debug_path = os.path.join(log_dir, snapshot_name)
        try:
            with open(debug_path, "w", encoding="utf-8") as dbg:
                dbg.write(res.text[:20000])  # first 20KB
            log(f"📝 Saved series snapshot: {debug_path}")
        except Exception as e:
            log(f"⚠️ Could not write series snapshot: {e}")

        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        nums = []
        for a in soup.find_all("a", href=True):
            m = CHAP_RE.search(a["href"])
            if m:
                try:
                    nums.append(int(m.group(1)))
                except ValueError:
                    pass
        best = max(nums) if nums else 1
        log(f"🔢 Latest chapter inferred: {best} (from {len(nums)} matches)")
        return best
    except Exception as e:
        log(f"❌ get_latest_chapter error: {e}")
        return 1

def gentle_autoscroll(driver, steps=20, pause=0.25):
    """Scrolls the page to trigger lazy-loaded images."""
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

def collect_image_urls(driver, base_url):
    """Collect image URLs from <img> (src, data-src, data-lazy-src, srcset) and <picture><source>."""
    # gentle scroll to trigger lazy-load
    gentle_autoscroll(driver, steps=24, pause=0.25)

    candidates = driver.find_elements(By.CSS_SELECTOR, "img, picture source")
    urls = []

    def add(url):
        if not url:
            return
        absu = urljoin(base_url, url)
        if absu not in urls:
            urls.append(absu)

    for el in candidates:
        tag = el.tag_name.lower()
        if tag == "img":
            for attr in ("src", "data-src", "data-lazy-src"):
                add(el.get_attribute(attr))
            srcset = el.get_attribute("srcset")
            if srcset:
                # use last (usually largest)
                last = srcset.split(",")[-1].strip().split()[0]
                add(last)
        elif tag == "source":
            srcset = el.get_attribute("srcset")
            if srcset:
                last = srcset.split(",")[-1].strip().split()[0]
                add(last)

    # keep only typical image extensions
    valid_exts = (".webp", ".jpg", ".jpeg", ".png", ".gif")
    urls = [u for u in urls if any(ext in u.lower() for ext in valid_exts)]

    return urls

# =======================================================================
# MAIN
# =======================================================================
start_time = time()
wait_for_connection()

for manhwa in manhwa_list:
    name       = manhwa["name"]
    base_url   = manhwa["url"]  # contains the series slug from manhwa_list.json
    url_format = f"{base_url}/chapter/{{}}"

    folder_path = os.path.join(pictures_base, name)
    os.makedirs(folder_path, exist_ok=True)

    log(f"\n📚 Processing manhwa: {name}")
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
                with open(src_file, encoding="utf-8") as f:
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

            log(f"🧭 Opening chapter page: {chap_url}")
            driver.get(chap_url)

            # Primary wait: original strict selector
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "img.object-cover.mx-auto")
                    )
                )
                log("⏳ Detected images via .object-cover.mx-auto")
            except Exception:
                # Fallback: any image on the page
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img"))
                )
                log("⏳ Fallback: detected generic <img> elements")

            image_urls = collect_image_urls(driver, chap_url)
            log(f"🖼️ Found {len(image_urls)} images on {chap_url}")

            if not image_urls:
                # Save DOM for debugging before failing
                try:
                    dom_dump = driver.page_source
                    dump_path = os.path.join(log_dir, f"{name}_chapter_{chap:03d}_dom.html")
                    with open(dump_path, "w", encoding="utf-8") as f:
                        f.write(dom_dump[:250_000])
                    log(f"📝 Saved DOM snapshot (no images found): {dump_path}")
                except Exception as e:
                    log(f"⚠️ Could not write DOM snapshot: {e}")
                raise Exception("No images found (after scroll & src/srcset checks)")

            os.makedirs(temp_folder, exist_ok=True)

            for i, src in enumerate(image_urls, start=1):
                try:
                    r = requests.get(src, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
                    r.raise_for_status()
                    ext = src.split("?")[0].split("#")[0].split(".")[-1].lower()
                    if ext not in ("webp", "jpg", "jpeg", "png", "gif"):
                        ext = "jpg"
                    file_name = f"{i:03d}.{ext}"
                    with open(os.path.join(temp_folder, file_name), "wb") as f:
                        f.write(r.content)
                    sleep(0.2)  # polite pause
                except Exception as e:
                    log(f"⚠️  Failed to fetch {src}: {e}")

            # Mark folder as ours
            with open(os.path.join(temp_folder, "source.txt"), "w", encoding="utf-8") as f:
                f.write("Downloaded from AsuraScans")

            # Replace old folder if needed
            if needs_replacement:
                shutil.rmtree(chap_folder, ignore_errors=True)

            os.rename(temp_folder, chap_folder)

            # Save DOM snapshot (first 250KB) for what Selenium actually saw
            try:
                dom_dump = driver.page_source
                dump_path = os.path.join(log_dir, f"{name}_chapter_{chap:03d}_dom.html")
                with open(dump_path, "w", encoding="utf-8") as f:
                    f.write(dom_dump[:250_000])
                log(f"📝 Saved DOM snapshot: {dump_path}")
            except Exception as e:
                log(f"⚠️ Could not write DOM snapshot: {e}")

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
