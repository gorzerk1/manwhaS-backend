import os
import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone as dt_timezone
from pytz import timezone
from urllib.parse import unquote

# === PATHS ===
json_path = "/home/ubuntu/server-backend/json/manhwa_list.json"
pictures_path = os.path.expanduser("~/backend/pictures")
log_dir = os.path.expanduser("~/backend/logs/searchNewChapters")

# === LOAD MANHWA LIST ===
with open(json_path, "r") as f:
    manhwa_list = json.load(f)

# === LOCAL CHAPTER FOR ASURA (backtrace source.txt) ===
def get_asura_latest_chapter(folder_path):
    chapters = sorted([
        int(m.group(1)) for m in
        (re.match(r"chapter-(\d+)", d) for d in os.listdir(folder_path))
        if m
    ], reverse=True)

    for chap_num in chapters:
        source_file = os.path.join(folder_path, f"chapter-{chap_num}", "source.txt")
        if os.path.exists(source_file):
            with open(source_file) as f:
                if "Downloaded from AsuraScans" in f.read():
                    return chap_num
    return None

# === LOCAL CHAPTER (default for other sources) ===
def get_local_latest_chapter(folder_path):
    chapter_nums = []
    for name in os.listdir(folder_path):
        match = re.match(r"chapter-(\d+)", name.lower())
        if match:
            chapter_nums.append(int(match.group(1)))
    return max(chapter_nums) if chapter_nums else None

# === ASURA URL FINDER ===
def fetch_asura_series_url(name):
    headers = {"User-Agent": "Mozilla/5.0"}
    base_url = "https://asuracomic.net"
    slug = name.lower().replace("-", "")

    def scan_page(url):
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        blocks = soup.select("div.w-full.p-1.pt-1.pb-3.border-b-\\[1px\\]")
        for block in blocks:
            a_tag = block.select_one("span.text-\\[15px\\] a[href]")
            if a_tag:
                href_clean = unquote(a_tag["href"]).lower().replace("-", "")
                if slug in href_clean:
                    return base_url + a_tag["href"]
        return None

    for i in range(0, 7):
        page_url = base_url if i == 0 else f"{base_url}/page/{i}"
        url = scan_page(page_url)
        if url:
            return url
    raise Exception("Series page not found on Asura")

# === ASURA LATEST CHAPTER ===
def extract_asura_latest_chapter(series_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(series_url, headers=headers, timeout=10)
    if res.status_code != 200:
        raise Exception("URL not valid")
    soup = BeautifulSoup(res.text, "html.parser")
    links = soup.select("div[class*='pl-4'][class*='border'] a[href*='/chapter/']")
    chapter_nums = [int(m.group(1)) for a in links if (m := re.search(r'/chapter/(\d{1,4})', a["href"]))]
    return max(chapter_nums) if chapter_nums else None

# === ONLINE CHAPTER CHECK ===
def check_online_chapter(name, data):
    global updated
    site = data.get("site")
    site_name = data.get("name", name)
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        if site == "asura":
            url = data.get("url")
            try:
                if url:
                    return extract_asura_latest_chapter(url)
                raise Exception("No valid URL")
            except:
                new_url = fetch_asura_series_url(name)
                chapter = extract_asura_latest_chapter(new_url)
                data["url"] = new_url
                updated = True
                return chapter

        elif site == "yaksha":
            url = f"https://yakshascans.com/manga/{site_name}"
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select("li.wp-manga-chapter a[href*='/chapter-']")
            return max([int(m.group(1)) for link in links if (m := re.search(r'/chapter-(\d{1,4})', link.get("href", "")))], default=None)

        elif site == "kunmanga":
            url = f"https://kunmanga.com/manga/{site_name}/"
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select("li.wp-manga-chapter a[href*='/chapter-']")
            return max([int(m.group(1)) for link in links if (m := re.search(r'chapter-(\d{1,4})', link.get("href", "")))], default=None)

        elif site == "manhwaclan":
            url = f"https://manhwaclan.com/manga/{site_name}/"
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select("div.listing-chapters_wrap a[href*='/chapter-']")
            return max([int(m.group(1)) for link in links if (m := re.search(r'/chapter-(\d+)', link.get("href", "")))], default=None)

        elif site == "manhuaplus":
            url = data.get("url")
            try:
                if not url:
                    search_slug = site_name.lower().replace(" ", "-").replace("_", "-")
                    base_url = "https://manhuaplus.org/all-manga/"
                    for page in range(1, 11):
                        res = requests.get(f"{base_url}{page}", headers=headers, timeout=10)
                        soup = BeautifulSoup(res.text, "html.parser")
                        grid = soup.select_one("div.grid.gtc-f141a.gg-20.p-13.mh-77vh")
                        if not grid:
                            continue
                        divs = grid.find_all("div", recursive=False)
                        for div in divs:
                            a_tag = div.find("a", href=True)
                            if not a_tag:
                                continue
                            href = a_tag["href"].lower()
                            if "/manga/" in href and search_slug in href:
                                match = re.match(r"(https://manhuaplus\.org/manga/[^/]+)", href)
                                if match:
                                    url = match.group(1)
                                    data["url"] = url
                                    updated = True
                                    break
                        if url:
                            break
                    if not url:
                        raise Exception("Could not find manhua URL on manhuaplus all-manga pages")

                res = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")
                links = soup.select("a[href*='/chapter-']")
                chapter_nums = []

                for link in links:
                    href = link.get("href", "")
                    text = link.text.strip()
                    # Try extract from href
                    m_href = re.search(r'/chapter-(\d{1,4})', href, re.IGNORECASE)
                    if m_href:
                        chapter_nums.append(int(m_href.group(1)))
                        continue
                    # Fallback to text
                    m_text = re.search(r'chapter\s*(\d{1,4})', text, re.IGNORECASE)
                    if m_text:
                        chapter_nums.append(int(m_text.group(1)))

                return max(chapter_nums) if chapter_nums else None

            except Exception as e:
                print(f"❌ Error checking manhuaplus for {site_name}: {e}")
                return None

            url = data.get("url")
            try:
                if not url:
                    search_slug = site_name.lower().replace(" ", "-").replace("_", "-")
                    base_url = "https://manhuaplus.org/all-manga/"
                    for page in range(1, 11):
                        res = requests.get(f"{base_url}{page}", headers=headers, timeout=10)
                        soup = BeautifulSoup(res.text, "html.parser")
                        grid = soup.select_one("div.grid.gtc-f141a.gg-20.p-13.mh-77vh")
                        if not grid:
                            continue
                        divs = grid.find_all("div", recursive=False)
                        for div in divs:
                            a_tag = div.find("a", href=True)
                            if not a_tag:
                                continue
                            href = a_tag["href"].lower()
                            if "/manga/" in href and search_slug in href:
                                match = re.match(r"(https://manhuaplus\.org/manga/[^/]+)", href)
                                if match:
                                    url = match.group(1)
                                    data["url"] = url
                                    updated = True
                                    break
                        if url:
                            break
                    if not url:
                        raise Exception("Could not find manhua URL on manhuaplus all-manga pages")

                res = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")
                links = soup.select("ul.main li.wp-manga-chapter a")
                chapter_nums = []

                for link in links:
                    href = link.get("href", "")
                    text = link.text.strip()
                    # Try to get chapter from href first
                    m_href = re.search(r'/chapter-(\d{1,4})', href, re.IGNORECASE)
                    if m_href:
                        chapter_nums.append(int(m_href.group(1)))
                        continue
                    # Fallback to text if href fails
                    m_text = re.search(r'chapter\s*(\d{1,4})', text, re.IGNORECASE)
                    if m_text:
                        chapter_nums.append(int(m_text.group(1)))

                return max(chapter_nums) if chapter_nums else None

            except Exception as e:
                print(f"❌ Error checking manhuaplus for {site_name}: {e}")
                return None

            url = data.get("url")
            try:
                if not url:
                    search_slug = site_name.lower().replace(" ", "-").replace("_", "-")
                    base_url = "https://manhuaplus.org/all-manga/"
                    for page in range(1, 11):
                        res = requests.get(f"{base_url}{page}", headers=headers, timeout=10)
                        soup = BeautifulSoup(res.text, "html.parser")
                        grid = soup.select_one("div.grid.gtc-f141a.gg-20.p-13.mh-77vh")
                        if not grid:
                            continue
                        divs = grid.find_all("div", recursive=False)
                        for div in divs:
                            a_tag = div.find("a", href=True)
                            if not a_tag:
                                continue
                            href = a_tag["href"].lower()
                            if "/manga/" in href and search_slug in href:
                                match = re.match(r"(https://manhuaplus\.org/manga/[^/]+)", href)
                                if match:
                                    url = match.group(1)
                                    data["url"] = url
                                    updated = True
                                    break
                        if url:
                            break
                    if not url:
                        raise Exception("Could not find manhua URL on manhuaplus all-manga pages")

                res = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")
                links = soup.select("ul.main li.wp-manga-chapter a")
                chapter_nums = [
                    int(m.group(1)) for link in links
                    if (m := re.search(r'chapter[^0-9]*?(\d{1,4})', link.text, re.IGNORECASE))
                ]
                return max(chapter_nums) if chapter_nums else None

            except Exception as e:
                print(f"❌ Error checking manhuaplus for {site_name}: {e}")
                return None

        elif site == "readkingdom":
            url = "https://ww5.readkingdom.com/manga/kingdom/"

            try:
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
            except Exception as e:
                raise Exception(f"Failed to fetch ReadKingdom page: {e}")

            soup = BeautifulSoup(res.text, "html.parser")
            all_blocks = soup.select("div.bg-bg-secondary.p-3.rounded.mb-3.shadow")

            valid_chapters = []
            for div in all_blocks:
                a_tag = div.select_one("a[href*='kingdom-chapter-']")
                label = div.select_one("div.text-xs.font-semibold.text-text-muted.uppercase")

                if not a_tag or not label or not label.text.strip():
                    continue

                match = re.search(r'kingdom-chapter-(\d{1,4})', a_tag["href"])
                if match:
                    valid_chapters.append(int(match.group(1)))

            return max(valid_chapters) if valid_chapters else None


    except Exception as e:
        print(f"❌ Error for {name} ({site}): {e}")
        return None

# === LOGGING ===
def log_new_chapter(name, site, local, online):
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "new_chapters.log"), "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {site} - {name}: Local {local} → Online {online}\n")

def log_no_new_chapters():
    os.makedirs(log_dir, exist_ok=True)
    msg = f"No new chapters found - {datetime.now(dt_timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} ({datetime.now(timezone('Israel')).strftime('%Y-%m-%d %H:%M:%S')} GMT+3)"
    print(msg)
    with open(os.path.join(log_dir, "new_chapters.log"), "a") as f:
        f.write(msg + "\n")

# === MAIN ===
if __name__ == "__main__":
    new_found = False
    printed_header = False
    updated = False

    for folder in manhwa_list:
        folder_path = os.path.join(pictures_path, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"📁 Created folder: {folder_path}")
        if os.path.isdir(folder_path):
            if not printed_header:
                print("_" * 86)
                printed_header = True
            entries = manhwa_list[folder]
            preferred_logged = False
            preferred_online = None

            for data in entries:
                site = data.get("site", "unknown")
                local_chapter = get_asura_latest_chapter(folder_path) if site == "asura" else get_local_latest_chapter(folder_path)
                online_chapter = check_online_chapter(folder, data)
                if online_chapter is not None and (not local_chapter or online_chapter > local_chapter):
                    tag = "(prefered)" if not preferred_logged else "(skipped)"
                    print(f"🆕 {site} - {folder}: New Chapter {online_chapter} {tag}")
                    if not preferred_logged:
                        log_new_chapter(folder, site, local_chapter, online_chapter)
                        new_found = True
                        preferred_logged = True
                        preferred_online = online_chapter
                else:
                    if preferred_logged and online_chapter == preferred_online:
                        print(f"🆕 {site} - {folder}: New Chapter {online_chapter} (skipped)")
                    else:
                        online_str = "❌ error" if online_chapter is None else online_chapter
                        print(f"✅ {site} - {folder}: No new chapter (Local: {local_chapter}, Online: {online_str})")
            print("_" * 86)

    if not new_found:
        log_no_new_chapters()

    if updated:
        with open(json_path, "w") as f:
            json.dump(manhwa_list, f, indent=2)
        print("📝 manhwa_list.json updated with fixed or missing URLs.")
