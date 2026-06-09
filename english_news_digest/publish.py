"""Local static file output and compatibility redirects."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .paths import DIST, DIST_ASSETS, DIST_EDITIONS
from .render.article import render_article_page
from .render.assets import write_assets
from .render.calendar import render_calendar_page
from .render.edition import render_edition_page
from .schemas import Edition

JST = ZoneInfo("Asia/Tokyo")


def redirect_html(target: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url={target}">
  <link rel="canonical" href="{target}">
  <title>Redirect</title>
</head>
<body>
  <p><a href="{target}">Continue</a></p>
</body>
</html>
"""


def publish_edition(
    edition: Edition,
    analyses: dict[str, dict],
    *,
    update_calendar: bool = True,
) -> None:
    if edition.status not in {"selected", "complete"}:
        raise RuntimeError(f"cannot publish edition with status {edition.status}")

    write_assets()

    edition_dist = DIST_EDITIONS / edition.edition_date
    articles_dist = edition_dist / "articles"
    staging = DIST / "_staging" / edition.edition_date
    staging_articles = staging / "articles"
    staging_articles.mkdir(parents=True, exist_ok=True)

    for record in edition.article_records:
        analysis = analyses.get(record.article_id)
        if not analysis:
            continue
        html_out = render_article_page(edition, record, analysis)
        out_path = staging_articles / f"{record.slug}.html"
        out_path.write_text(html_out, encoding="utf-8")

    generated = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    edition_html = render_edition_page(edition, analyses, generated)
    (staging / "index.html").write_text(edition_html, encoding="utf-8")
    (staging / "edition.json").write_text(
        json.dumps(edition.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    edition_dist.parent.mkdir(parents=True, exist_ok=True)
    if edition_dist.exists():
        shutil.rmtree(edition_dist)
    shutil.move(str(staging), str(edition_dist))
    staging_parent = staging.parent
    if staging_parent.exists() and not any(staging_parent.iterdir()):
        staging_parent.rmdir()

    _write_compat_redirects(edition)

    if update_calendar:
        rebuild_calendar(edition.edition_date)

    edition.status = "complete"


def _write_compat_redirects(edition: Edition) -> None:
    day_redirect = DIST / "days" / f"{edition.edition_date}.html"
    day_redirect.parent.mkdir(parents=True, exist_ok=True)
    target = f"../editions/{edition.edition_date}/index.html"
    day_redirect.write_text(redirect_html(target), encoding="utf-8")

    old_articles = DIST / "articles" / edition.edition_date
    old_articles.mkdir(parents=True, exist_ok=True)
    for record in edition.article_records:
        target = f"../../editions/{edition.edition_date}/articles/{record.slug}.html"
        path = old_articles / f"{record.slug}.html"
        path.write_text(redirect_html(target), encoding="utf-8")
        deep_path = old_articles / f"{record.slug}.deep.html"
        if deep_path.is_file():
            deep_path.write_text(redirect_html(target), encoding="utf-8")


def load_calendar_index() -> dict:
    path = DIST / "calendar.json"
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data.get("editions"), list):
            editions_dict = {}
            for entry in data["editions"]:
                date = entry.get("date", "")
                if date:
                    editions_dict[date] = {
                        "status": "complete",
                        "article_count": entry.get("article_count", 0),
                        "japan_count": entry.get("japan_count", 0),
                        "world_count": entry.get("world_count", 0),
                        "path": entry.get("url", f"editions/{date}/index.html").replace(
                            "days/", "editions/"
                        ).replace(".html", "/index.html"),
                        "generated_at": "",
                    }
            return {"editions": editions_dict}
        return data
    return {"editions": {}}


def rebuild_calendar(focus_date: str | None = None) -> None:
    from .select import EDITIONS_DIR, load_edition

    index = load_calendar_index()
    editions_map = index.get("editions", {})

    if EDITIONS_DIR.is_dir():
        for edition_dir in sorted(EDITIONS_DIR.iterdir()):
            if not edition_dir.is_dir():
                continue
            edition = load_edition(edition_dir.name)
            if edition and edition.status == "complete":
                editions_map[edition.edition_date] = {
                    "status": "complete",
                    "article_count": edition.actual_article_count,
                    "japan_count": edition.category_counts.get("japan", 0),
                    "world_count": edition.category_counts.get("world", 0),
                    "path": f"editions/{edition.edition_date}/index.html",
                    "generated_at": edition.generated_at,
                }

    index["editions"] = editions_map
    calendar_path = DIST / "calendar.json"
    calendar_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    focus = focus_date or datetime.now(JST).strftime("%Y-%m-%d")
    index_html = render_calendar_page(index, focus)
    (DIST / "index.html").write_text(index_html, encoding="utf-8")
