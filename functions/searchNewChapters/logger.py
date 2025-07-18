from datetime import datetime, timezone as dt_timezone

from pytz import timezone

from . import config


def log_new_chapter(name: str, site: str, local: int | None, online: int) -> None:
    config.log_dir.mkdir(parents=True, exist_ok=True)
    line = (
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {site} - {name}: "
        f"Local {local} → Online {online}\n"
    )
    (config.log_dir / "new_chapters.log").open("a").write(line)
    print(f"🆕 {site} - {name}: New Chapter {online}")


def log_no_new_chapters() -> None:
    config.log_dir.mkdir(parents=True, exist_ok=True)
    utc_time   = datetime.now(dt_timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    local_time = datetime.now(timezone("Israel")).strftime("%Y-%m-%d %H:%M:%S")
    msg = f"No new chapters found - {utc_time} ({local_time} GMT+3)"
    print(msg)
    (config.log_dir / "new_chapters.log").open("a").write(msg + "\n")
