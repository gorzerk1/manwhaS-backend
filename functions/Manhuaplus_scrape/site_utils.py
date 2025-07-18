import requests
from bs4 import BeautifulSoup

def get_latest_chapter(base_url: str) -> int:
    try:
        resp = requests.get(base_url,
                            headers={"User-Agent": "Mozilla/5.0"},
                            timeout=10)
        soup  = BeautifulSoup(resp.text, "html.parser")
        nums  = []

        for a in soup.select("a[href*='/chapter-']"):
            href  = a.get("href", "")
            part  = href.split("/chapter-")[-1].split("/")[0]
            if part.isdigit():
                nums.append(int(part))

        return max(nums) if nums else 1
    except Exception as exc:
        print(f"❌ get_latest_chapter error: {exc}")
        return 1
