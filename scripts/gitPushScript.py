import os
import subprocess
from dotenv import load_dotenv

# === Load GitHub Token from .env ===
load_dotenv(dotenv_path=os.path.expanduser("~/importantFold/.env"))
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    raise Exception("❌ GITHUB_TOKEN missing in .env")

# === Paths ===
REPO_PATH = os.path.expanduser("~/server-backend")
FILES_TO_CHECK = [
    "json/manhwa_list.json",
    "json/manwha_details.json"
]
REMOTE_URL = f"https://{TOKEN}@github.com/gorzerk1/manwhaS-backend.git"

# === Pull latest from GitHub ===
def git_pull():
    subprocess.run(["git", "pull"], cwd=REPO_PATH, check=True)

# === Set remote with token ===
def set_git_remote():
    subprocess.run(["git", "remote", "set-url", "origin", REMOTE_URL], cwd=REPO_PATH, check=True)

# === Check if files changed ===
def is_file_changed():
    result = subprocess.run(["git", "status", "--porcelain"] + FILES_TO_CHECK, cwd=REPO_PATH, stdout=subprocess.PIPE, text=True)
    return bool(result.stdout.strip())

# === Commit and Push ===
def git_push():
    subprocess.run(["git", "add"] + FILES_TO_CHECK, cwd=REPO_PATH, check=True)
    subprocess.run(["git", "commit", "-m", "update manhwa json files"], cwd=REPO_PATH, check=True)
    subprocess.run(["git", "push"], cwd=REPO_PATH, check=True)
    print("🚀 Pushed to GitHub.")

# === Main ===
if __name__ == "__main__":
    git_pull()
    set_git_remote()

    if is_file_changed():
        print("✅ manhwa JSON files changed. Pushing...")
        git_push()
    else:
        print("⏭ No changes. Nothing to push.")
