import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://asuracomic.net"


def fetch_asura_series_url(name: str) -> str:
    # Clean the input name to match the format in href
    slug = name.lower().replace("-", "").replace(" ", "")

    def scan_one(url: str):
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.raise_for_status()
        except Exception as e:
            print(f"❌ Failed to load {url}: {e}")
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        # Find span with class "text-[15px] font-medium", then <a href="/series/...">
        a_tags = soup.select("span.text-\\[15px\\].font-medium a[href^='/series/']")

        for a in a_tags:
            href_clean = unquote(a["href"]).lower().replace("-", "").replace(" ", "")
            if slug in href_clean:
                return BASE_URL + a["href"]

        return None

    # Try home page and up to 6 paginated pages
    for i in range(0, 7):
        url = BASE_URL if i == 0 else f"{BASE_URL}/page/{i}"
        found = scan_one(url)
        if found:
            return found

    raise Exception(f"Series page not found on Asura for '{name}'")

def extract_asura_latest_chapter(series_url: str) -> int | None:
    res = requests.get(series_url, headers=HEADERS, timeout=10)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    container = soup.select_one("div.grid.grid-cols-2.px-4.py-4.gap-2\\.5")
    if not container:
        print("❌ Could not find the chapter container.")
        return None

    links = container.select("a[href*='/chapter/']")

    chapter_nums = [
        int(m.group(1))
        for a in links
        if (m := re.search(r"/chapter/(\d+)", a["href"]))
    ]

    return max(chapter_nums) if chapter_nums else None
