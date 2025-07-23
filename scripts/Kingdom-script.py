import os
import requests
from time import sleep, time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Clean up previous sessions
os.system("pkill -f chrome")
os.system("pkill -f chromedriver")
os.system("pkill -f chromium")
os.system("pkill -f HeadlessChrome")
os.system("pkill -f selenium")

# --- Setup
manga_name = "kingdom"
chapter_slug = "kingdom-chapter"
base_domains = [f"https://ww{i}.readkingdom.com" for i in range(1, 8)]

base_dir = os.path.expanduser("~/backend")
pictures_base = os.path.join(base_dir, "pictures", manga_name)
log_base = os.path.join(base_dir, "logs")

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
log_folder = os.path.join(log_base, timestamp)
os.makedirs(log_folder, exist_ok=True)

# --- Chrome options
chrome_options = Options()
# Remove headless mode for debugging:
# chrome_options.add_argument("--headless")
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
working_domain = None

def try_download(chapter_url):
    print(f"🌐 Trying URL: {chapter_url}")
    try:
        # HEAD check
        res = session.head(chapter_url, headers=headers, timeout=5)
        print(f"🔍 HEAD status: {res.status_code}")
        if res.status_code != 200:
            print("❌ Page not reachable")
            return []

        driver.set_page_load_timeout(20)
        driver.get(chapter_url)

        # Wait for images to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.mb-3.mx-auto.js-page"))
            )
        except:
            print("⚠️ Timeout waiting for images to appear")

        # Get image elements
        img_elements = driver.find_elements(By.CSS_SELECTOR, "img.mb-3.mx-auto.js-page")
        print(f"🖼️ Found {len(img_elements)} <img> elements")

        valid_exts = [".jpg", ".jpeg", ".png", ".webp"]
        img_urls = []
        for img in img_elements:
            src = img.get_attribute("src")
            if src:
                clean_url = src.split("?")[0]
                if any(clean_url.lower().endswith(ext) for ext in valid_exts):
                    img_urls.append(src)

        print(f"✅ Filtered valid image URLs: {len(img_urls)}")
        return img_urls

    except Exception as e:
        print(f"⚠️ Exception: {e}")
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

# --- Get existing chapters
existing = {
    int(name.replace("chapter-", ""))
    for name in os.listdir(pictures_base)
    if name.startswith("chapter-") and os.path.isdir(os.path.join(pictures_base, name))
}
max_existing = max(existing) if existing else 0
print(f"⏭️ Skipped {len(existing)} chapters already downloaded (up to chapter {max_existing})")

chapter = 1
while True:
    while chapter in existing:
        chapter += 1

    chapter_dir = os.path.join(pictures_base, f"chapter-{chapter}")
    print(f"\n📚 Chapter {chapter}")
    img_urls = []
    final_url = None

    # Try domains
    if working_domain:
        base_url = working_domain
        for suffix in [f"{chapter_slug}-{chapter:03d}", f"{chapter_slug}-{chapter}"]:
            test_url = f"{base_url}/chapter/{suffix}/"
            img_urls = try_download(test_url)
            if len(img_urls) > 0:
                final_url = test_url
                break
    else:
        for base_url in base_domains:
            for suffix in [f"{chapter_slug}-{chapter:03d}", f"{chapter_slug}-{chapter}"]:
                test_url = f"{base_url}/chapter/{suffix}/"
                img_urls = try_download(test_url)
                if len(img_urls) > 0:
                    final_url = test_url
                    working_domain = base_url
                    break
            if final_url:
                break

    if not final_url:
        print(f"🚫 No valid images found for chapter {chapter}. Likely last chapter.")
        break

    print(f"✅ Found {len(img_urls)} images from: {final_url}")
    os.makedirs(chapter_dir, exist_ok=True)

    for i, img_url in enumerate(img_urls):
        ext = img_url.split('.')[-1].split('?')[0]
        name = f"{i+1:03d}.{ext}"
        path = os.path.join(chapter_dir, name)
        try:
            res = session.get(img_url, headers=headers, timeout=30)
            total_downloaded_bytes += len(res.content)
            with open(path, "wb") as f:
                f.write(res.content)
            print(f"✅ Saved: {name}")
        except Exception as e:
            print(f"❌ Failed: {img_url} | Error: {e}")

    downloaded_gb = round(total_downloaded_bytes / 1024 / 1024 / 1024, 5)
    current_total_gb = get_total_dir_size_gb(pictures_base)
    print(f"📦 Downloaded this run: {downloaded_gb:.5f} GB")
    print(f"💾 Total stored: {current_total_gb:.5f} GB")

    log_lines.append(f"[Chapter {chapter}] ✅ Done from {final_url}")
    existing.add(chapter)
    chapter += 1

# --- Final log
log_path = os.path.join(log_folder, f"{manga_name}.txt")
with open(log_path, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

driver.quit()
os.system("pkill -f chrome")
os.system("pkill -f chromedriver")
os.system("pkill -f chromium")
os.system("pkill -f HeadlessChrome")
os.system("pkill -f selenium")

print(f"\n✅ Finished in {time() - start_time:.2f} sec")
