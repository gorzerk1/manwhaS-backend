from pathlib import Path

from . import local_chapters, asura_helpers, site_lookups


def check_online_chapter(series_name: str, entry: dict) -> tuple[int | None, int | None]:
    site = entry.get("site", "unknown")
    folder_path = Path(entry["folder_path"])

    # ── 1) local side ─────────────────────────────────────────────────────────
    if site == "asura":
        local = local_chapters.get_asura_latest_chapter(folder_path)
    else:
        local = local_chapters.get_local_latest_chapter(folder_path)

    print(f"[DEBUG] Local latest for '{series_name}' ({site}): {local}")

    # ── 2) online side ────────────────────────────────────────────────────────
    if site == "asura":
        url = entry.get("url")
        online = asura_helpers.extract_asura_latest_chapter(url) if url else None

        if online is None:
            print(f"[DEBUG] No online data found, attempting repair for '{series_name}'...")
            try:
                entry["url"] = asura_helpers.fetch_asura_series_url(series_name)
                online = asura_helpers.extract_asura_latest_chapter(entry["url"])
                print(f"[DEBUG] Repair successful. Online latest: {online}")
            except Exception as e:
                print(f"❌ Asura lookup failed for {series_name}: {e}")
                online = None
        else:
            print(f"[DEBUG] Online latest for '{series_name}' (asura): {online}")

    else:
        func = getattr(site_lookups, f"{site}_latest", None)
        if func:
            slug = entry.get("name", series_name)
            online = func(slug, entry)
            print(f"[DEBUG] Online latest for '{series_name}' ({site}): {online}")
        else:
            print(f"❌ No scraper implemented for site '{site}'")
            online = None

    # ── 3) update decision ────────────────────────────────────────────────────
    if online is None:
        print(f"[DEBUG] '{series_name}' → Cannot update (online missing).")
    elif local is None or online > local:
        print(f"[DEBUG] '{series_name}' → Update available: local={local}, online={online}")
    else:
        print(f"[DEBUG] '{series_name}' → Already up-to-date: local={local}, online={online}")

    return local, online
