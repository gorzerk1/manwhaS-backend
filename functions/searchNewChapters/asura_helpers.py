import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://asuracomic.net"


def fetch_asura_series_url(name: str) -> str:
    """
    Try to locate the series page on Asura by scanning page 1…6.
    Returns the full URL (raises Exception if nothing found).
    """
    slug = name.lower().replace("-", "").replace(" ", "")

    def scan_one(url: str):
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.raise_for_status()
        except Exception as e:
            print(f"❌ Failed to load {url}: {e}")
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        a_tags = soup.select(
            "div.w-full.p-1.pt-1.pb-3.border-b-\\[1px\\] a[href^='/series/']"
        )

        for a in a_tags:
            href_clean = unquote(a["href"]).lower().replace("-", "").replace(" ", "")
            if slug in href_clean:
                return BASE_URL + a["href"]
        return None

    # page 0 is home, then /page/1 … /page/6
    for i in range(0, 7):
        url = BASE_URL if i == 0 else f"{BASE_URL}/page/{i}"
        found = scan_one(url)
        if found:
            return found

    raise Exception(f"Series page not found on Asura for '{name}'")


def extract_asura_latest_chapter(series_url: str) -> int | None:
    """
    Scrape the chapter list on a series page and return the highest number.
    """
    res = requests.get(series_url, headers=HEADERS, timeout=10)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    links = soup.select("div[class*='pl-4'][class*='border'] a[href*='/chapter/']")
    chapter_nums = [
        int(m.group(1))
        for a in links
        if (m := re.search(r"/chapter/(\d{1,4})", a["href"]))
    ]
    return max(chapter_nums) if chapter_nums else None
