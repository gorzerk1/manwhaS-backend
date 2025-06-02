import os
import requests
from time import sleep, time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


os.system("pkill -f chrome")
os.system("pkill -f chromedriver")
os.system("pkill -f chromium")
os.system("pkill -f HeadlessChrome")
os.system("pkill -f selenium")

# === CONFIG ===
base_dir = os.path.expanduser("~/backend")
pictures_base = os.path.join(base_dir, "pictures", "demon-magic-emperor")
log_base = os.path.join(base_dir, "logs")
check_url = "https://manhuaplus.org"

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
log_folder = os.path.join(log_base, timestamp)
os.makedirs(log_folder, exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument('--user-agent=Mozilla/5.0')

def start_browser():
    return webdriver.Chrome(options=chrome_options)

driver = start_browser()

def wait_for_connection():
    while True:
        try:
            res = requests.get(check_url, timeout=10)
            if res.status_code == 200:
                print("✅ Website is reachable.")
                return
        except:
            print("❌ Can't connect. Retrying...")
        sleep(10)

# === MAIN ===
start_time = time()
wait_for_connection()

chapter = 1
log_lines = []
session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0"}

while True:
    chapter_url = f"https://manhuaplus.org/manga/demon-magic-emperor/chapter-{chapter}"
    chapter_dir = os.path.join(pictures_base, f"chapter-{chapter}")
    print(f"\n📚 Chapter {chapter}")

    if os.path.exists(chapter_dir):
        print("⏭️ Skipped (exists)")
        chapter += 1
        continue

    try:
        print("🌀 Loading chapter page...")
        try:
            driver.get(chapter_url)
        except Exception as e:
            print(f"⚠️ Browser crashed: {e} — restarting...")
            driver.quit()
            driver = start_browser()
            driver.get(chapter_url)

        print("⏳ Waiting for JS content...")
        sleep(2)

        print("🔍 Finding image links...")
        links = driver.find_elements(By.CSS_SELECTOR, "a.readImg")
        img_urls = [a.get_attribute("href") for a in links if a.get_attribute("href")]

        print(f"📸 Found {len(img_urls)} images")

        if not img_urls:
            print("⚠️ No images found. Likely last chapter.")
            break

        os.makedirs(chapter_dir, exist_ok=True)

        for i, img_url in enumerate(img_urls):
            ext = img_url.split('.')[-1].split('?')[0]
            name = f"{i+1:03d}.{ext}"
            path = os.path.join(chapter_dir, name)

            try:
                t0 = time()
                res = session.get(img_url, headers=headers, timeout=30)
                with open(path, "wb") as f:
                    f.write(res.content)
                print(f"✅ Saved {name} in {time() - t0:.2f}s")
            except Exception as e:
                print(f"❌ Failed {img_url} - {e}")

        log_lines.append(f"[Chapter {chapter}] ✅ Done")
        chapter += 1

    except Exception as e:
        print(f"❌ Fatal error at Chapter {chapter}: {e}")
        break

# === Save Log ===
log_path = os.path.join(log_folder, "demon-magic-emperor.txt")
with open(log_path, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

driver.quit()
print(f"\n⏱️ Finished in {time() - start_time:.2f} sec")
