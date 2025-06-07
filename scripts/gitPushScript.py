import os
import json
import subprocess
from dotenv import load_dotenv

# === ENV ===
load_dotenv(dotenv_path=os.path.expanduser("~/importantFold/.env"))
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    raise Exception("❌ GITHUB_TOKEN is missing in .env")

# === CONFIG ===
REPO_PATH = os.path.expanduser("~/server-backend")
JSON_FILE = os.path.join(REPO_PATH, "json", "manhwa_list.json")
REMOTE_URL = f"https://{TOKEN}@github.com/gorzerk1/manwhaS-backend.git"

# === FUNCTIONS ===
def set_git_remote():
    subprocess.run(["git", "remote", "set-url", "origin", REMOTE_URL], cwd=REPO_PATH, check=True)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def update_manhwa_list(slug, site, url):
    data = load_json(JSON_FILE)
    sources = data.get(slug, [])
    
    # Remove old entry for the same site
    new_sources = [s for s in sources if s.get("site") != site]
    new_sources.append({"site": site, "url": url})

    # If nothing changed, skip
    if sources == new_sources:
        print(f"⏭ No change for {slug}")
        return False

    data[slug] = new_sources
    save_json(JSON_FILE, data)
    print(f"✅ Updated: {slug}")
    return True

def push_changes(file_rel_path, msg):
    subprocess.run(["git", "add", file_rel_path], cwd=REPO_PATH, check=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=REPO_PATH, check=True)
    subprocess.run(["git", "push"], cwd=REPO_PATH, check=True)
    print("🚀 GitHub push complete")

# === MAIN ===
if __name__ == "__main__":
    slug = "example_slug"
    site = "asura"
    url = "https://asura.com/manga/example"

    set_git_remote()
    if update_manhwa_list(slug, site, url):
        push_changes("json/manhwa_list.json", f"update {slug} url")
