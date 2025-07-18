import requests
from time import sleep

def wait_for_connection(url: str, retry_sec: int = 300) -> None:
    while True:
        try:
            if requests.get(url, timeout=10).status_code == 200:
                print("✅  Website is reachable.")
                return
        except Exception:
            pass
        print(f"❌  Can't connect to {url}.  Retrying in {retry_sec//60} min…")
        sleep(retry_sec)
