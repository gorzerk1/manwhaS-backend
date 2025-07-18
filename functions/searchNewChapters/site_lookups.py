import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


# ──────────────────────────────────────────────────────────────────────────────
def yaksha_latest(slug: str, _entry: dict) -> int | None:
    url = f"https://yakshascans.com/manga/{slug}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.select("li.wp-manga-chapter a[href*='/chapter-']")
        return max(
            (
                int(m.group(1))
                for link in links
                if (m := re.search(r"/chapter-(\d{1,4})", link.get("href", "")))
            ),
            default=None,
        )
    except Exception as e:
        print(f"❌ yaksha - {slug}: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
def kunmanga_latest(slug: str, _entry: dict) -> int | None:
    url = f"https://kunmanga.com/manga/{slug}/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.select("li.wp-manga-chapter a[href*='/chapter-']")
        return max(
            (
                int(m.group(1))
                for link in links
                if (m := re.search(r"chapter-(\d{1,4})", link.get("href", "")))
            ),
            default=None,
        )
    except Exception as e:
        print(f"❌ kunmanga - {slug}: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
def manhwaclan_latest(slug: str, _entry: dict) -> int | None:
    url = f"https://manhwaclan.com/manga/{slug}/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.select("div.listing-chapters_wrap a[href*='/chapter-']")
        return max(
            (
                int(m.group(1))
                for link in links
                if (m := re.search(r"/chapter-(\d+)", link.get("href", "")))
            ),
            default=None,
        )
    except Exception as e:
        print(f"❌ manhwaclan - {slug}: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
def manhuaplus_latest(slug: str, entry: dict) -> int | None:
    try:
        # ── Part 1 – find URL if needed ───────────────────────────────────────
        url = entry.get("url")
        if not url:
            search_slug = slug.lower().replace(" ", "-").replace("_", "-")
            base = "https://manhuaplus.org/all-manga/"
            for page in range(1, 11):
                res = requests.get(f"{base}{page}", headers=HEADERS, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")
                grid = soup.select_one("div.grid.gtc-f141a.gg-20.p-13.mh-77vh")
                if not grid:
                    continue
                for div in grid.find_all("div", recursive=False):
                    a = div.find("a", href=True)
                    if not a:
                        continue
                    href = a["href"].lower()
                    if "/manga/" in href and search_slug in href:
                        m = re.match(r"(https://manhuaplus\.org/manga/[^/]+)", href)
                        if m:
                            url = m.group(1)
                            entry["url"] = url
                            break
                if url:
                    break
        if not url:
            print(f"❌ manhuaplus - {slug}: Series URL not found.")
            return None

        # ── Part 2 – find latest chapter from 'comicBtn' ─────────────────────
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        latest_button = soup.find("a", class_="comicBtn mb-6 fs-13 r4 i-block w-m2p4 is-primary")
        if latest_button and (href := latest_button.get("href", "")):
            # Extract the chapter number from the href
            if (m := re.search(r"/chapter-(\d+)", href, re.IGNORECASE)):
                return int(m.group(1))

        print(f"❌ manhuaplus - {slug}: Could not find latest chapter button.")
        return None

    except Exception as e:
        print(f"❌ manhuaplus - {slug}: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
def readkingdom_latest(_slug: str, _entry: dict) -> int | None:
    url = "https://ww5.readkingdom.com/manga/kingdom/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        blocks = soup.select("div.bg-bg-secondary.p-3.rounded.mb-3.shadow")
        chapters = []
        for div in blocks:
            a = div.select_one("a[href*='kingdom-chapter-']")
            label = div.select_one("div.text-xs.font-semibold.text-text-muted.uppercase")
            if not a or not label or not label.text.strip():
                continue
            if (m := re.search(r"kingdom-chapter-(\d{1,4})", a["href"])):
                chapters.append(int(m.group(1)))
        return max(chapters) if chapters else None
    except Exception as e:
        print(f"❌ readkingdom: {e}")
        return None
