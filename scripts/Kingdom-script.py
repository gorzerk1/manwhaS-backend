import os
import requests
import logging
from time import sleep, time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

for proc in ["chrome", "chromedriver", "chromium", "HeadlessChrome", "selenium"]:
    os.system(f"pkill -f {proc}")
    logging.debug(f"Attempted to kill any running process: {proc}")

manga_name = "kingdom"
chapter_slug = "kingdom-chapter"
base_domains = [f"https://ww{i}.readkingdom.com" for i in range(1, 8)]
logging.debug(f"Base domains: {base_domains}")

base_dir = os.path.expanduser("~/backend")
pictures_base = os.path.join(base_dir, "pictures", manga_name)
log_base = os.path.join(base_dir, "logs")

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
log_folder = os.path.join(log_base, timestamp)
os.makedirs(log_folder, exist_ok=True)
logging.debug(f"Log folder created: {log_folder}")

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument('--user-agent=Mozilla/5.0')

def start_browser():
    logging.debug("Starting headless Chrome browser")
    return webdriver.Chrome(options=chrome_options)

driver = start_browser()
session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0"}

start_time = time()
log_lines = []
total_downloaded_bytes = 0
working_domain = None

def try_download(chapter_url):
    logging.debug(f"Trying download from URL: {chapter_url}")
    try:
        res = session.head(chapter_url, headers=headers, timeout=5)
        logging.debug(f"HEAD status {res.status_code} for {chapter_url}")
        if res.status_code != 200:
            return []

        driver.set_page_load_timeout(15)
        driver.get(chapter_url)
        logging.debug(f"Page loaded: {chapter_url}")
        sleep(15)

        img_elements = driver.find_elements(By.CSS_SELECTOR, "img.mb-3.mx-auto.js-page")
        logging.debug(f"Found {len(img_elements)} img elements")

        valid_exts = [".jpg", ".jpeg", ".png", ".webp"]
        img_urls = []
        for img in img_elements:
            src = img.get_attribute("src")
            if src:
                clean_url = src.split("?")[0]
                if any(clean_url.lower().endswith(ext) for ext in valid_exts):
                    img_urls.append(src)
                    logging.debug(f"Valid image URL: {src}")

        return img_urls
    except Exception as e:
        logging.exception(f"Exception in try_download for {chapter_url}: {e}")
        return []

def get_total_dir_size_gb(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            try:
                file_size = os.path.getsize(os.path.join(dirpath, f))
                total += file_size
            except Exception as e:
                logging.debug(f"Error getting size for {f}: {e}")
    return round(total / 1024 / 1024 / 1024, 5)

existing = {
    int(name.replace("chapter-", ""))
    for name in os.listdir(pictures_base)
    if name.startswith("chapter-") and os.path.isdir(os.path.join(pictures_base, name))
}
max_existing = max(existing) if existing else 0
print(f"⏭️ Skipped {len(existing)} chapters already downloaded (up to chapter {max_existing})")
logging.debug(f"Existing chapters: {existing}")

chapter = 1
while True:
    while chapter in existing:
        chapter += 1

    chapter_dir = os.path.join(pictures_base, f"chapter-{chapter}")
    logging.debug(f"Processing Chapter {chapter}")
    print(f"\n📚 Chapter {chapter}")
    img_urls = []
    final_url = None

    if working_domain:
        base_url = working_domain
        logging.debug(f"Using working domain: {base_url}")
        for suffix in [f"{chapter_slug}-{chapter:03d}", f"{chapter_slug}-{chapter}"]:
            test_url = f"{base_url}/chapter/{suffix}/"
            logging.debug(f"Testing URL: {test_url}")
            img_urls = try_download(test_url)
            if len(img_urls) > 4:
                final_url = test_url
                break
    else:
        for base_url in base_domains:
            logging.debug(f"Trying base domain: {base_url}")
            for suffix in [f"{chapter_slug}-{chapter:03d}", f"{chapter_slug}-{chapter}"]:
                test_url = f"{base_url}/chapter/{suffix}/"
                logging.debug(f"Testing URL: {test_url}")
                img_urls = try_download(test_url)
                if len(img_urls) > 4:
                    final_url = test_url
                    working_domain = base_url
                    logging.debug(f"Working domain set: {working_domain}")
                    break
            if final_url:
                break

    if not final_url:
        print("🚫 No valid images found. Likely last chapter.")
        logging.debug("No valid images; terminating loop")
        break

    print(f"✅ Found {len(img_urls)} images. Downloading...")
    os.makedirs(chapter_dir, exist_ok=True)

    for i, img_url in enumerate(img_urls):
        ext = img_url.split('.')[-1].split('?')[0]
        name = f"{i+1:03d}.{ext}"
        path = os.path.join(chapter_dir, name)
        try:
            logging.debug(f"Downloading {img_url} to {path}")
            res = session.get(img_url, headers=headers, timeout=30)
            total_downloaded_bytes += len(res.content)
            with open(path, "wb") as f:
                f.write(res.content)
            print(f"✅ {name}")
        except Exception as e:
            print(f"❌ Failed {img_url}")
            logging.exception(f"Failed to download {img_url}: {e}")

    downloaded_gb = round(total_downloaded_bytes / 1024 / 1024 / 1024, 5)
    current_total_gb = get_total_dir_size_gb(pictures_base)
    logging.debug(f"Downloaded this run (GB): {downloaded_gb}")
    logging.debug(f"Total stored (GB): {current_total_gb}")
    print(f"📦 Downloaded this run: {downloaded_gb:.5f} GB")
    print(f"💾 Total stored: {current_total_gb:.5f} GB")

    log_lines.append(f"[Chapter {chapter}] ✅ Done from {final_url}")
    existing.add(chapter)
    chapter += 1

log_path = os.path.join(log_folder, f"{manga_name}.txt")
with open(log_path, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))
logging.debug(f"Log written to {log_path}")

driver.quit()
for proc in ["chrome", "chromedriver", "chromium", "HeadlessChrome", "selenium"]:
    os.system(f"pkill -f {proc}")
    logging.debug(f"Cleaned up process: {proc}")

print(f"\n✅ Finished in {time() - start_time:.2f} sec")
