import json
import os
import subprocess

# Path to JSON file
json_path = os.path.expanduser("~/server-backend/json/manhwa_list.json")

# Load latest Git version
def git_pull():
    subprocess.run(["git", "pull"], cwd=os.path.expanduser("~/server-backend"), check=True)

# Load old data
def load_existing():
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Save + push if changed
def save_if_changed(new_data):
    old_data = load_existing()

    if old_data == new_data:
        print("⏭ No changes, not pushing.")
        return

    print("✅ Changes detected. Updating file...")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2)

    # Push
    subprocess.run(["git", "add", "json/manhwa_list.json"], cwd=os.path.expanduser("~/server-backend"), check=True)
    subprocess.run(["git", "commit", "-m", "update manhwa_list with new urls"], cwd=os.path.expanduser("~/server-backend"), check=True)
    subprocess.run(["git", "push"], cwd=os.path.expanduser("~/server-backend"), check=True)
    print("🚀 Pushed to GitHub.")

# === USAGE ===
git_pull()

# `manhwa_list` is your final scraped result at the end
# Replace this with your actual dict
from your_scraper import manhwa_list

save_if_changed(manhwa_list)
