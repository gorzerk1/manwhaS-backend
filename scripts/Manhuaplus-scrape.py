import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from time import time

from functions.Manhuaplus_scrape import (
    kill_zombie_chrome,
    load_manhwa_list,
    make_log_folder,
    CHECK_URL,
    wait_for_connection,
    download_manhwa,
)


def main() -> None:
    start = time()

    kill_zombie_chrome()


    wait_for_connection(CHECK_URL)

    manhwa_list = load_manhwa_list()
    log_folder  = make_log_folder()

    all_errors: list[str] = []
    for m in manhwa_list:
        all_errors.extend(download_manhwa(m, log_folder))

    dur = time() - start
    print(f"\n⏱️  Finished in {dur:.2f} s")
    if all_errors:
        print("\n⚠️  Some chapters failed:")
        for line in all_errors:
            print("  •", line)


if __name__ == "__main__":
    main()
