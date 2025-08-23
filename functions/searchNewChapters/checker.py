# checker.py
from pathlib import Path
import logging
import os
import traceback
from typing import Callable, Optional, Tuple

from . import local_chapters, asura_helpers, site_lookups

# ── logging setup ─────────────────────────────────────────────────────────────
DEBUG = os.getenv("DEBUG", "0") == "1"
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
log = logging.getLogger("checker")

def check_online_chapter(
    series_name: str,
    entry: dict,
    *,
    on_repair: Optional[Callable[[str, dict, Optional[str], str], None]] = None,
) -> Tuple[Optional[int], Optional[int]]:
    """
    Check local vs. online latest chapter.

    Args:
      series_name: Display name of the series.
      entry: Dict with at least keys: site, folder_path, (optional) url, name.
      on_repair: Optional callback invoked ONLY when the Asura URL is repaired.
                 Signature: (series_name, entry, old_url, new_url) -> None

    Returns:
      (local_latest, online_latest)
    """
    site = entry.get("site", "unknown")
    folder_path = Path(entry["folder_path"])

    log.info(f"[check] series='{series_name}' site='{site}' folder='{folder_path}'")
    log.debug(f"[check] entry in: {entry!r}")

    # ── 1) local side ─────────────────────────────────────────────────────────
    try:
        if site == "asura":
            local = local_chapters.get_asura_latest_chapter(folder_path)
        else:
            local = local_chapters.get_local_latest_chapter(folder_path)
        log.info(f"[local] latest={local}")
    except Exception as e:
        log.error(f"[local] failed to get latest for {folder_path}: {e}")
        if DEBUG:
            log.debug(traceback.format_exc())
        local = None

    # ── 2) online side ────────────────────────────────────────────────────────
    online: Optional[int]
    if site == "asura":
        url = entry.get("url")
        log.debug(f"[online] asura url (before)={url}")

        try:
            online = asura_helpers.extract_asura_latest_chapter(url) if url else None
            log.info(f"[online] asura latest (from url)={online}")
        except Exception as e:
            log.warning(f"[online] extract failed for url={url}: {e}")
            if DEBUG:
                log.debug(traceback.format_exc())
            online = None

        # Try to repair missing/wrong URL
        if online is None:
            old_url = url
            try:
                repaired = asura_helpers.fetch_asura_series_url(series_name)
                entry["url"] = repaired
                log.info(f"[repair] asura url repaired: {old_url} → {repaired}")

                try:
                    online = asura_helpers.extract_asura_latest_chapter(repaired)
                    log.info(f"[online] asura latest (after repair)={online}")
                except Exception as e:
                    log.warning(f"[online] extract failed after repair: {e}")
                    if DEBUG:
                        log.debug(traceback.format_exc())
                    online = None

                # optional persistence hook
                if on_repair:
                    try:
                        on_repair(series_name, entry, old_url, repaired)
                        log.debug("[repair] on_repair callback executed.")
                    except Exception as e:
                        log.warning(f"[repair] on_repair callback failed: {e}")
                        if DEBUG:
                            log.debug(traceback.format_exc())

            except Exception as e:
                log.error(f"[repair] Asura lookup failed for '{series_name}': {e}")
                if DEBUG:
                    log.debug(traceback.format_exc())
                online = None

    else:
        func = getattr(site_lookups, f"{site}_latest", None)
        if func:
            slug = entry.get("name", series_name)
            try:
                online = func(slug, entry)
                log.info(f"[online] {site} latest={online} (slug='{slug}')")
            except Exception as e:
                log.error(f"[online] {site} lookup failed for '{slug}': {e}")
                if DEBUG:
                    log.debug(traceback.format_exc())
                online = None
        else:
            log.error(f"[online] No scraper implemented for site '{site}'")
            online = None

    log.debug(f"[check] result → local={local}, online={online}")
    return local, online
