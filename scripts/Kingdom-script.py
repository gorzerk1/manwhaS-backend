import os
import requests
from time import sleep, time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Kill any zombie browser processes before starting
os.system("pkill -f chrome")
os.system("pkill -f chromedriver")
os.system("pkill -f chromium")
os.system("pkill -f HeadlessChrome")
os.system("pkill -f selenium")

# === CONFIG ===
manga_name = "kingdom"
base_url = "https://ww4.readkingdom.com"
chapter_slug = "kingdom-chapter"
base_dir = os.path.expanduser("~/backend")
pictures_base = os.path.join(base_dir, "pictures", manga_name)
log_base = os.path.join(base_dir, "logs")

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

driver = start_browser()
session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0"}

start_time = time()
log_lines = []
total_downloaded_bytes = 0

def try_download(chapter_url):
    try:
        res = session.head(chapter_url, headers=headers, timeout=5)
        if res.status_code != 200:
            return []
        driver.set_page_load_timeout(15)
        driver.get(chapter_url)
        sleep(2)
        img_elements = driver.find_elements(By.CSS_SELECTOR, "div.text-center img")
        valid_exts = [".jpg", ".jpeg", ".png", ".webp"]
        img_urls = [img.get_attribute("src") for img in img_elements if img.get_attribute("src")]
        img_urls = [url for url in img_urls if any(url.lower().endswith(ext) for ext in valid_exts)]
        return img_urls
    except:
        return []

def get_total_dir_size_gb(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, f))
            except:
                continue
    return round(total / 1024 / 1024 / 1024, 5)

# Scan already existing chapters
existing = {
    int(name.replace("chapter-", ""))
    for name in os.listdir(pictures_base)
    if name.startswith("chapter-") and os.path.isdir(os.path.join(pictures_base, name))
}
max_existing = max(existing) if existing else 0
print(f"⏭️ Skipped {len(existing)} chapters already downloaded (up to chapter {max_existing})")

# Start from first missing
chapter = 1
while True:
    while chapter in existing:
        chapter += 1

    chapter_dir = os.path.join(pictures_base, f"chapter-{chapter}")
    print(f"\n📚 Chapter {chapter}")

    print("🔀 Trying padded URL...")
    padded_url = f"{base_url}/chapter/{chapter_slug}-{chapter:03d}/"
    img_urls = try_download(padded_url)

    if len(img_urls) <= 1:
        print("⚠️ No images or only 1. Trying fallback URL...")
        fallback_url = f"{base_url}/chapter/{chapter_slug}-{chapter}/"
        img_urls = try_download(fallback_url)

    if len(img_urls) <= 1:
        print("⚠️ No valid images for padded or fallback. Likely last chapter.")
        break

    if len(img_urls) <= 4:
        print(f"⚠️ Too few images ({len(img_urls)}). Skipping.")
        chapter += 1
        continue

    print(f"📸 Found {len(img_urls)} images")
    os.makedirs(chapter_dir, exist_ok=True)

    for i, img_url in enumerate(img_urls):
        ext = img_url.split('.')[-1].split('?')[0]
        name = f"{i+1:03d}.{ext}"
        path = os.path.join(chapter_dir, name)
        try:
            t0 = time()
            res = session.get(img_url, headers=headers, timeout=30)
            total_downloaded_bytes += len(res.content)
            with open(path, "wb") as f:
                f.write(res.content)
            print(f"✅ Saved {name} in {time() - t0:.2f}s")
        except Exception as e:
            print(f"❌ Failed {img_url} - {e}")

    downloaded_gb = round(total_downloaded_bytes / 1024 / 1024 / 1024, 5)
    current_total_gb = get_total_dir_size_gb(pictures_base)
    print(f"📦 Total downloaded this run: {downloaded_gb:.5f} GB")
    print(f"💾 Total stored in EC2 (pictures folder): {current_total_gb:.5f} GB")

    log_lines.append(f"[Chapter {chapter}] ✅ Done")
    existing.add(chapter)
    chapter += 1

# Save log
log_path = os.path.join(log_folder, f"{manga_name}.txt")
with open(log_path, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

driver.quit()
os.system("pkill -f chrome")
os.system("pkill -f chromedriver")
os.system("pkill -f chromium")
os.system("pkill -f HeadlessChrome")
os.system("pkill -f selenium")

print(f"\n⏱️ Finished in {time() - start_time:.2f} sec")
