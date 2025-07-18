from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def _chrome_options() -> Options:
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--user-agent=Mozilla/5.0")
    return opts


def start_browser() -> webdriver.Chrome:
    """Return a ready‑to‑use headless Chrome driver."""
    return webdriver.Chrome(options=_chrome_options())
