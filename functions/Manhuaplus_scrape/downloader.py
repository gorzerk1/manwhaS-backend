from __future__ import annotations

import os
import shutil
from time import sleep
from typing import List

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .browser_utils import start_browser
from .site_utils     import get_latest_chapter
from .config         import PICTURES_BASE


def _save_image(url: str, folder: str, index: int) -> None:
    ext = url.split(".")[-1].split("?")[0]
    name = f"{index:03d}.{ext}"
    path = os.path.join(folder, name)
    content = requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                           timeout=10).content
    with open(path, "wb") as f:
        f.write(content)
    sleep(0.3)  # light throttle to be polite


def download_manhwa(
    manhwa: dict,
    log_folder: str,
    max_retries: int = 5,
) -> List[str]:
    """
    Download every chapter for the provided `manhwa` dict:

        {"name": "...", "url": "https://manhuaplus.org/manga/..."}.

    A text log is written inside `log_folder`.
    Returns a list of error strings (empty on perfect run).
    """
    name      = manhwa["name"]
    base_url  = manhwa["url"]
    url_fmt   = f"{base_url}/chapter-{{}}"
    target_dir = os.path.join(PICTURES_BASE, name)
    os.makedirs(target_dir, exist_ok=True)

    last_chapter = get_latest_chapter(base_url)
    log_lines: list[str] = []
    errors:    list[str] = []

    print(f"\n📚  Processing: {name}   (latest = {last_chapter})")

    # ------------------------------------------------------------------
    for chap in range(1, last_chapter + 1):
        chap_dir  = os.path.join(target_dir, f"chapter-{chap}")
        chap_url  = url_fmt.format(chap)

        if os.path.exists(chap_dir):
            print(f"⏭️  Chapter {chap} exists  ➜  skip")
            log_lines.append(f"[Chapter {chap}] Skipped (already there)")
            continue

        print(f"📅  Downloading Chapter {chap} …")
        success = False

        for attempt in range(1, max_retries + 1):
            driver = None
            try:
                driver = start_browser()
                driver.set_page_load_timeout(60)
                driver.set_script_timeout(30)

                driver.get(chap_url)
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.readImg"))
                )
                links  = driver.find_elements(By.CSS_SELECTOR, "a.readImg")
                images = [a.get_attribute("href") for a in links if a.get_attribute("href")]

                if not images:
                    raise RuntimeError("No images found on page")

                os.makedirs(chap_dir, exist_ok=True)
                for idx, src in enumerate(images, start=1):
                    _save_image(src, chap_dir, idx)

                with open(os.path.join(chap_dir, "source.txt"), "w") as f:
                    f.write("Downloaded from ManhuaPlus")

                log_lines.append(f"[Chapter {chap}] ✅ Done")
                success = True
                break  # break retry‑loop

            except Exception as exc:
                print(f"❌  Attempt {attempt}/{max_retries} failed: {exc}")
                sleep(3)

            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass

        # ------- post‑retry cleanup -----------------------------------
        if not success:
            errors.append(f"{name} Chapter {chap}: failed after retries")
            log_lines.append(f"[Chapter {chap}] ❌ Failed")
            if os.path.exists(chap_dir):
                print(f"🧹  Removing failed folder: {chap_dir}")
                shutil.rmtree(chap_dir, ignore_errors=True)

    # ------- write per‑title log --------------------------------------
    log_path = os.path.join(log_folder, f"{name}.txt")
    with open(log_path, "w", encoding="utf‑8") as fp:
        fp.write(f"📚 Log for: {name}\n\n")
        fp.write("\n".join(log_lines))

    print(f"📝  Log saved ➜  {log_path}")
    return errors
