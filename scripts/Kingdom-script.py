#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import logging
from time import sleep, time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# ── basic logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

for proc in ["chrome", "chromedriver", "chromium", "HeadlessChrome", "selenium"]:
    os.system(f"pkill -f {proc}")
    logging.debug("Attempted to kill any running process: %s", proc)

# ── user‑config bits ────────────────────────────────────────────────────────────
manga_name   = "kingdom"
chapter_slug = "kingdom-chapter"

# only mirrors that resolve today
base_domains = [
    "https://ww1.readkingdom.com",
    "https://ww2.readkingdom.com",
    "https://ww3.readkingdom.com",
    "https://ww4.readkingdom.com",
    "https://ww5.readkingdom.com",
]

base_dir   = os.path.expanduser("~/backend")
pic_root   = os.path.join(base_dir, "pictures", manga_name)
log_root   = os.path.join(base_dir, "logs")

timestamp  = datetime.now().strftime("%Y-%m-%d_%H-%M")
log_folder = os.path.join(log_root, timestamp)
os.makedirs(log_folder, exist_ok=True)

# ── headless Chrome options ─────────────────────────────────────────────────────
chrome_opts = Options()
chrome_opts.add_argument("--headless=new")
chrome_opts.add_argument("--disable-gpu")
chrome_opts.add_argument("--window-size=1920x1080")
chrome_opts.add_argument("--no-sandbox")
chrome_opts.add_argument("--disable-dev-shm-usage")
chrome_opts.add_argument("--user-agent=Mozilla/5.0")

def start_browser():
    logging.debug("Starting headless Chrome browser")
    return webdriver.Chrome(options=chrome_opts)

driver  = start_browser()
session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0"}

start_time  = time()
total_bytes = 0
log_lines   = []
working_dom = None

# ── helper: total dir size in GiB ───────────────────────────────────────────────
def dir_size_gib(path: str) -> float:
    total = 0
    for dpath, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(dpath, f))
            except OSError:
                continue
    return round(total / 1024 / 1024 / 1024, 5)

# ── helper: download&scrape one chapter url ─────────────────────────────────────
def try_download(ch_url: str) -> list[str]:
    logging.debug("Trying download from URL: %s", ch_url)
    try:
        # follow 301/302 automatically now
        res = session.head(ch_url, headers=headers,
                           allow_redirects=True, timeout=5)
        logging.debug("HEAD status %s for %s", res.status_code, ch_url)
        if res.status_code != 200:
            return []

        # give the page longer to load
        driver.set_page_load_timeout(60)
        try:
            driver.get(ch_url)
        except TimeoutException:
            # stop loading; whatever finished is enough to parse the DOM
            logging.warning("Page‑load timeout, stopping load: %s", ch_url)
            driver.execute_script("window.stop()")

        sleep(2)  # short pause – DOM has settled

        imgs = driver.find_elements(By.CSS_SELECTOR, "img.mb-3.mx-auto.js-page")
        logging.debug("Found %d <img> tags", len(imgs))

        valid = [".jpg", ".jpeg", ".png", ".webp"]
        urls  = []
        for img in imgs:
            src = img.get_attribute("src") or ""
            clean = src.split("?", 1)[0].lower()
            if any(clean.endswith(ext) for ext in valid):
                urls.append(src)
                logging.debug("Valid image URL: %s", src)

        return urls
    except Exception as e:
        logging.exception("Exception in try_download for %s: %s", ch_url, e)
        return []

# ── find already‑downloaded chapters ────────────────────────────────────────────
os.makedirs(pic_root, exist_ok=True)
existing = {
    int(name.replace("chapter-", ""))
    for name in os.listdir(pic_root)
    if name.startswith("chapter-") and
       os.path.isdir(os.path.join(pic_root, name))
}
max_existing = max(existing) if existing else 0
print(f"⏭️  Skipped {len(existing)} chapters (up to {max_existing})")
logging.debug("Existing chapters: %s", existing)

# ── main loop ───────────────────────────────────────────────────────────────────
chapter = 1
while True:
    # skip any chapter we already have
    while chapter in existing:
        chapter += 1

    chapter_dir = os.path.join(pic_root, f"chapter-{chapter}")
    print(f"\n📚 Chapter {chapter}")
    logging.debug("Processing Chapter %d", chapter)

    img_urls, final_url = [], None

    # first try the last good domain, else iterate the list
    dom_list = [working_dom] if working_dom else base_domains
    for base in dom_list:
        if base is None:
            continue
        for slug in (f"{chapter_slug}-{chapter:03d}",
                     f"{chapter_slug}-{chapter}"):
            url = f"{base}/chapter/{slug}/"
            imgs = try_download(url)
            if len(imgs) > 4:
                img_urls, final_url = imgs, url
                working_dom = base
                break
        if final_url:
            break

    if not final_url:
        print("🚫 No valid images found. Likely last chapter.")
        logging.debug("No valid images; terminating loop.")
        break

    print(f"✅ Found {len(img_urls)} images. Downloading…")
    os.makedirs(chapter_dir, exist_ok=True)

    for idx, img_url in enumerate(img_urls, start=1):
        ext  = img_url.split(".")[-1].split("?")[0]
        name = f"{idx:03d}.{ext}"
        path = os.path.join(chapter_dir, name)
        try:
            logging.debug("Downloading %s → %s", img_url, path)
            res = session.get(img_url, headers=headers, timeout=30)
            total_bytes += len(res.content)
            with open(path, "wb") as fh:
                fh.write(res.content)
            print(f"  ✅ {name}")
        except Exception as e:
            print(f"  ❌ {img_url}")
            logging.exception("Failed to download %s: %s", img_url, e)

    run_gib  = round(total_bytes / 1024 / 1024 / 1024, 5)
    total_gb = dir_size_gib(pic_root)
    print(f"📦  Downloaded this run: {run_gib:.5f} GB")
    print(f"💾  Total stored:       {total_gb:.5f} GB")

    log_lines.append(f"[Chapter {chapter}] ✅ from {final_url}")
    existing.add(chapter)
    chapter += 1

# ── write session log ───────────────────────────────────────────────────────────
log_path = os.path.join(log_folder, f"{manga_name}.txt")
with open(log_path, "w", encoding="utf-8") as fh:
    fh.write("\n".join(log_lines))
logging.debug("Log written to %s", log_path)

# ── tidy up ─────────────────────────────────────────────────────────────────────
driver.quit()
for proc in ["chrome", "chromedriver", "chromium", "HeadlessChrome", "selenium"]:
    os.system(f"pkill -f {proc}")
    logging.debug("Cleaned up process: %s", proc)

print(f"\n✅ Finished in {time() - start_time:.2f} s")
