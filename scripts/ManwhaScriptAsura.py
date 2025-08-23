#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import uuid
import shutil
import traceback
import subprocess
from time import sleep, time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ------------------------------ CONFIG ------------------------------------

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

# ------------------------------ LOGGING ------------------------------------

log_handle = open(log_path, "a", encoding="utf-8", buffering=1)

def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    log_handle.write(line + "\n")

def run_cmd(cmd: list[str]) -> tuple[int,str,str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"

def debug_env():
    log("===== DEBUG: ENVIRONMENT =====")
    log(f"User: {os.geteuid()} / {os.getlogin() if hasattr(os, 'getlogin') else 'n/a'}")
    code, out, _ = run_cmd(["uname", "-a"])
    log(f"uname -a: {out if out else 'n/a'}")
    log(f"Python: {sys.version.split()[0]}")
    try:
        import selenium
        log(f"Selenium: {selenium.__version__}")
    except Exception:
        log("Selenium: unknown")

    for name in ["CHROME_BIN", "GOOGLE_CHROME_BIN", "CHROMIUM_BIN", "CHROMEDRIVER", "PATH"]:
        val = os.environ.get(name)
        if name == "PATH" and val:
            val = val.split(":")
        log(f"ENV {name}: {val}")

    # which binaries
    for b in ["google-chrome", "chrome", "chromium", "chromium-browser", "chromedriver"]:
        code, out, _ = run_cmd(["which", b])
        log(f"which {b}: {out if out else 'not found'}")

    # versions
    for b in [["google-chrome","--version"],["chromium","--version"],["chromium-browser","--version"],["chromedriver","--version"]]:
        code, out, err = run_cmd(b)
        log(f"{' '.join(b)} → rc={code} out='{out}' err='{err}'")

def debug_psnote(title=""):
    code, out, _ = run_cmd(["ps","-ef"])
    lines = [ln for ln in out.splitlines() if any(k in ln for k in ["chrome","chromium","HeadlessChrome","chromedriver"])]
    log(f"===== DEBUG: PROCESSES {title} =====")
    if not lines:
        log("No chrome/chromedriver processes found.")
    else:
        for ln in lines[-40:]:
            log(ln)

def debug_profile_dir(profile_dir: str):
    log(f"===== DEBUG: PROFILE DIR =====")
    log(f"profile_dir: {profile_dir} exists={os.path.isdir(profile_dir)}")
    if os.path.isdir(profile_dir):
        try:
            entries = os.listdir(profile_dir)
        except Exception as e:
            entries = []
            log(f"listdir error: {e}")
        locks = [e for e in entries if e.startswith("Singleton")]
        log(f"entries: {len(entries)} items; singleton locks: {locks if locks else 'none'}")
        for fn in locks:
            p = os.path.join(profile_dir, fn)
            try:
                st = os.stat(p)
                log(f"  {fn}: size={st.st_size} mtime={datetime.fromtimestamp(st.st_mtime)}")
            except Exception as e:
                log(f"  {fn}: stat error: {e}")

# ------------------------------ PRE-CLEAN ----------------------------------

# Don't kill system Chrome blindly anymore; just show it:
debug_psnote("before start")

# ------------------------------ LOAD LIST ----------------------------------

with open(json_path, "r", encoding="utf-8") as f:
    full_data = json.load(f)

manhwa_list = []
for name, sources in full_data.items():
    for entry in sources:
        if entry.get("site") == "asura":
            url = entry.get("url")
            if isinstance(url, str) and url.startswith("https://asuracomic.net/series/"):
                manhwa_list.append({"name": name, "url": url})
                log(f"Loaded series URL for '{name}': {url}")
            else:
                log(f"Missing or invalid URL for: {name}")

# ------------------------------ BROWSER ------------------------------------

def base_chrome_options(profile_dir: str, headless_flag: str) -> Options:
    opts = Options()
    if headless_flag == "new":
        opts.add_argument("--headless=new")
    elif headless_flag == "classic":
        opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920x1080")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--user-agent=Mozilla/5.0")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(f"--user-data-dir={profile_dir}")
    opts.add_argument("--profile-directory=Default")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--password-store=basic")
    opts.add_argument("--use-mock-keychain")
    opts.add_argument("--remote-debugging-port=0")
    # Allow custom binary override if provided via env
    chrome_bin = os.environ.get("CHROME_BIN") or os.environ.get("GOOGLE_CHROME_BIN") or os.environ.get("CHROMIUM_BIN")
    if chrome_bin:
        opts.binary_location = chrome_bin
    return opts

def start_browser():
    debug_env()
    profile_dir = os.path.join(profiles_root, f"profile-{uuid.uuid4().hex}")
    os.makedirs(profile_dir, exist_ok=False)
    debug_profile_dir(profile_dir)

    # log file per attempt
    driver_log1 = os.path.join(log_dir, "chromedriver_headless_new.log")
    driver_log2 = os.path.join(log_dir, "chromedriver_headless_classic.log")

    # Attempt 1: headless=new
    log("Attempt 1: launching Chrome with --headless=new")
    try:
        opts1 = base_chrome_options(profile_dir, "new")
        service = webdriver.ChromeService(log_output=open(driver_log1, "w"))
    except AttributeError:
        # Selenium < 4.10 compatibility
        from selenium.webdriver.chrome.service import Service as ChromeService
        service = ChromeService(log_path=driver_log1)
        opts1 = base_chrome_options(profile_dir, "new")
    try:
        driver = webdriver.Chrome(options=opts1, service=service)
        driver._profile_dir = profile_dir
        log("Attempt 1: SUCCESS")
        return driver
    except Exception as e1:
        log("Attempt 1: FAILED")
        log("Exception:\n" + "".join(traceback.format_exception(e1)))
        debug_profile_dir(profile_dir)
        debug_psnote("after attempt 1")
        try:
            with open(driver_log1, "r", encoding="utf-8", errors="ignore") as lf:
                tail = lf.readlines()[-200:]
                log("chromedriver log (tail) attempt 1:\n" + "".join(tail))
        except Exception as e:
            log(f"could not read {driver_log1}: {e}")

    # Attempt 2: headless (classic)
    log("Attempt 2: launching Chrome with classic --headless")
    try:
        opts2 = base_chrome_options(profile_dir, "classic")
        service2 = webdriver.ChromeService(log_output=open(driver_log2, "w"))
    except AttributeError:
        from selenium.webdriver.chrome.service import Service as ChromeService
        service2 = ChromeService(log_path=driver_log2)
        opts2 = base_chrome_options(profile_dir, "classic")
    try:
        driver = webdriver.Chrome(options=opts2, service=service2)
        driver._profile_dir = profile_dir
        log("Attempt 2: SUCCESS")
        return driver
    except Exception as e2:
        log("Attempt 2: FAILED")
        log("Exception:\n" + "".join(traceback.format_exception(e2)))
        debug_profile_dir(profile_dir)
        debug_psnote("after attempt 2")
        try:
            with open(driver_log2, "r", encoding="utf-8", errors="ignore") as lf:
                tail = lf.readlines()[-200:]
                log("chromedriver log (tail) attempt 2:\n" + "".join(tail))
        except Exception as e:
            log(f"could not read {driver_log2}: {e}")

    # Hard fail; keep profile dir so you can inspect it
    log(f"Both attempts failed. Leaving profile dir for inspection: {profile_dir}")
    raise RuntimeError("Chrome could not be started; see logs above.")

# ------------------------------ HELPERS ------------------------------------

def wait_for_connection():
    log("Checking site reachability…")
    while True:
        try:
            res = requests.get(check_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            log(f"Reachability HTTP {res.status_code}")
            if res.status_code == 200:
                log("Site is reachable.")
                return
        except Exception as e:
            log(f"Reachability error: {e}; retry in 5 min")
        sleep(300)

CHAP_RE = re.compile(r"/chapter/(\d+)(?:[/?#]|$)")

def get_latest_chapter(base_url: str) -> int:
    try:
        log(f"Fetching series HTML: {base_url}")
        res = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        log(f"Series HTTP {res.status_code}; bytes={len(res.text)}")
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
        log(f"Inferred latest chapter: {best} (matches: {len(nums)})")
        return best
    except Exception as e:
        log(f"get_latest_chapter error: {e}")
        return 1

def gentle_autoscroll(driver, steps=24, pause=0.2):
    last_h = -1
    for _ in range(steps):
        driver.execute_script("window.scrollBy(0, Math.ceil(window.innerHeight*0.9));")
        sleep(pause)
        h = driver.execute_script("return Math.max(document.body.scrollTop, document.documentElement.scrollTop);")
        if h == last_h:
            break
        last_h = h

def collect_image_urls(driver):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.object-cover.mx-auto")))
    except Exception:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img, picture source")))
    gentle_autoscroll(driver, steps=24, pause=0.2)
    candidates = driver.find_elements(By.CSS_SELECTOR, "img.object-cover.mx-auto, picture source, picture img, img")
    urls = []
    def add(u):
        if not u:
            return
        lu = u.lower()
        if any(ext in lu for ext in [".webp",".jpg",".jpeg",".png",".gif"]):
            if u not in urls:
                urls.append(u)
    for el in candidates:
        tag = el.tag_name.lower()
        if tag == "img":
            for attr in ("currentSrc", "src", "data-src", "data-lazy-src"):
                add(el.get_attribute(attr))
            srcset = el.get_attribute("srcset")
            if srcset:
                last_item = srcset.split(",")[-1].strip().split()[0]
                add(last_item)
        elif tag == "source":
            srcset = el.get_attribute("srcset")
            if srcset:
                last_item = srcset.split(",")[-1].strip().split()[0]
                add(last_item)
    log(f"Collected {len(urls)} image URLs on chapter page")
    return urls

# ------------------------------ MAIN ---------------------------------------

start = time()
debug_env()
wait_for_connection()

for manhwa in manhwa_list:
    name      = manhwa["name"]
    base_url  = manhwa["url"]
    url_format = f"{base_url}/chapter/{{}}"

    folder_path = os.path.join(pictures_base, name)
    os.makedirs(folder_path, exist_ok=True)

    log(f"\n=== Processing: {name} ===")
    last_chapter = get_latest_chapter(base_url)

    driver = None
    try:
        driver = start_browser()
        # timeouts
        try:
            driver.set_page_load_timeout(60)
            driver.set_script_timeout(30)
        except Exception as e:
            log(f"Timeout setup error: {e}")

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
                log(f"Open chapter: {chap_url}")
                driver.get(chap_url)
                image_urls = collect_image_urls(driver)
                if not image_urls:
                    raise Exception("No images found after scroll/srcset checks")
                os.makedirs(temp_folder, exist_ok=True)
                for i, src in enumerate(image_urls, start=1):
                    ext = src.split("?")[0].split("#")[0].split(".")[-1].lower()
                    if ext not in ("webp","jpg","jpeg","png","gif"):
                        ext = "jpg"
                    file_name = f"{i:03d}.{ext}"
                    resp = requests.get(src, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                    with open(os.path.join(temp_folder, file_name), "wb") as f:
                        f.write(resp.content)
                    sleep(0.15)
                with open(os.path.join(temp_folder, "source.txt"), "w") as f:
                    f.write("Downloaded from AsuraScans")
                if needs_replacement:
                    shutil.rmtree(chap_folder, ignore_errors=True)
                os.rename(temp_folder, chap_folder)
                log(f"✅ Downloaded {name} chapter {chap}")
            except Exception as e:
                shutil.rmtree(temp_folder, ignore_errors=True)
                log(f"❌ {name} chapter {chap} – {e}\n{traceback.format_exc()}")

    except Exception as outer:
        log(f"❌ Failed to start/use browser for series '{name}': {outer}\n{traceback.format_exc()}")
    finally:
        if driver:
            try:
                debug_psnote("before quit()")
                driver.quit()
                log("driver.quit() called")
            except Exception as e:
                log(f"driver.quit() error: {e}")
            try:
                if hasattr(driver, "_profile_dir"):
                    pd = driver._profile_dir
                    debug_profile_dir(pd)
                    sleep(0.6)
                    shutil.rmtree(pd, ignore_errors=True)
                    log(f"Deleted profile dir: {pd}")
            except Exception as e:
                log(f"profile cleanup error: {e}")

# ------------------------------ DONE ---------------------------------------

log_handle.close()
print(f"\nFinished in {time() - start:.2f} sec")
