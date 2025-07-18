from pathlib import Path
import sys


project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from functions.searchNewChapters import config, checker, logger

if __name__ == "__main__":
    manhwa_list = config.load_manhwa_list()
    new_found = False

    for series_name, entries in manhwa_list.items():
        folder_path = Path(config.pictures_path) / series_name
        folder_path.mkdir(parents=True, exist_ok=True)

        for entry in entries:
            entry["folder_path"] = str(folder_path)          # pass to checker
            local, online = checker.check_online_chapter(series_name, entry)

            if online and (local is None or online > local):
                logger.log_new_chapter(series_name, entry.get("site"), local, online)
                new_found = True
            else:
                online_txt = "❌ error" if online is None else online
                print(
                    f"✅ {entry.get('site')} - {series_name}: "
                    f"No new chapter (Local: {local}, Online: {online_txt})"
                )

    if not new_found:
        logger.log_no_new_chapters()

    config.save_manhwa_list(manhwa_list)