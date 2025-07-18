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

    # ── 2) online side ────────────────────────────────────────────────────────
    if site == "asura":
        url = entry.get("url")
        online = (
            asura_helpers.extract_asura_latest_chapter(url) if url else None
        )
        if online is None:
            # try to repair missing / wrong URL
            try:
                entry["url"] = asura_helpers.fetch_asura_series_url(series_name)
                online = asura_helpers.extract_asura_latest_chapter(entry["url"])
            except Exception as e:
                print(f"❌ Asura lookup failed for {series_name}: {e}")
                online = None
    else:
        func = getattr(site_lookups, f"{site}_latest", None)
        if func:
            slug = entry.get("name", series_name)
            online = func(slug, entry)
        else:
            print(f"❌ No scraper implemented for site '{site}'")
            online = None

    return local, online
