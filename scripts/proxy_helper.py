import requests
from bs4 import BeautifulSoup
import random

# Free proxy list (can expand)
PROXIES = [
    "https://51.158.68.68:8811",
    "http://51.91.157.66:80",
    "http://64.225.8.97:9981",
    "http://165.225.77.41:10605",
    "http://200.105.215.18:33630"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TEST_URL = "https://asuracomic.net/series/swordmasters-youngest-son-049dcf42"

def test_connection(url, proxy=None):
    try:
        res = requests.get(url, headers=HEADERS, proxies=proxy, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "No title"
        return f"✅ Success [{proxy if proxy else 'No Proxy'}]: {title}"
    except Exception as e:
        return f"❌ Failed [{proxy if proxy else 'No Proxy'}]: {e}"

def get_working_proxy():
    for proxy_url in PROXIES:
        proxy = {"http": proxy_url, "https": proxy_url}
        try:
            res = requests.get(TEST_URL, headers=HEADERS, proxies=proxy, timeout=10)
            if res.status_code == 200:
                return proxy
        except:
            continue
    return None

if __name__ == "__main__":
    print("🔍 Testing direct connection...")
    print(test_connection(TEST_URL))

    print("\n🔁 Trying with proxies...")
    for proxy_url in PROXIES:
        proxy = {"http": proxy_url, "https": proxy_url}
        print(test_connection(TEST_URL, proxy))
