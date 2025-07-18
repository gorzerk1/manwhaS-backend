import os

_KILL_PATTERNS = [
    "chrome",
    "chromedriver",
    "chromium",
    "HeadlessChrome",
    "selenium",
]

def kill_zombie_chrome() -> None:
    for pat in _KILL_PATTERNS:
        os.system(f"pkill -f {pat}")
