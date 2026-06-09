"""Migrate legacy prototype data into edition + v2 analysis caches."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .analyze import analysis_cache_path, save_analysis
from .feeds import FeedArticle, fetch_all_feeds, is_japan_related, published_jst_date
from .normalize import make_article_id, rank_slug, slugify
from .paths import LEGACY_DATA_DIR
from .schemas import ArticleRecord, Edition, upgrade_analysis_to_v2
from .select import save_edition

JST = ZoneInfo("Asia/Tokyo")


def _parse_legacy_html_meta(html_path: Path) -> dict[str, str]:
    text = html_path.read_text(encoding="utf-8")
    title_m = re.search(r"<h1>([^<]+)</h1>", text)
    meta_m = re.search(r'<div class="meta">([^<]+)</div>', text)
    link_m = re.search(r'href="(https?://[^"]+)"[^>]*>元記事', text)
    badge_m = re.search(r'<span class="badge (\w+)">', text)
    return {
        "title": title_m.group(1) if title_m else "",
        "meta": meta_m.group(1) if meta_m else "",
        "source_url": link_m.group(1) if link_m else "",
        "category": badge_m.group(1) if badge_m else "japan",
    }


def _match_feed_article(
    title: str,
    source_url: str,
    feed_articles: list[FeedArticle],
) -> FeedArticle | None:
    for article in feed_articles:
        if article.link == source_url:
            return article
    title_key = slugify(title)
    for article in feed_articles:
        if slugify(article.title) == title_key:
            return article
    for article in feed_articles:
        if article.title.lower() == title.lower():
            return article
    return None


def migrate_legacy_edition(edition_date: str) -> Edition | None:
    legacy_dir = LEGACY_DATA_DIR / edition_date
    dist_articles = Path(__file__).resolve().parent.parent / "dist" / "articles" / edition_date
    if not legacy_dir.is_dir() or not dist_articles.is_dir():
        return None

    slugs: list[str] = []
    for path in sorted(dist_articles.glob("*.html")):
        if path.name.endswith(".deep.html"):
            continue
        slugs.append(path.stem)

    if not slugs:
        return None

    print(f"Migrating legacy edition {edition_date} ({len(slugs)} articles)...")
    feed_articles = fetch_all_feeds()

    records: list[ArticleRecord] = []
    article_ids: list[str] = []

    for rank, slug in enumerate(slugs, start=1):
        html_path = dist_articles / f"{slug}.html"
        meta = _parse_legacy_html_meta(html_path)
        feed = _match_feed_article(meta["title"], meta["source_url"], feed_articles)

        if feed:
            article_id = make_article_id(feed)
            source = feed.source
            source_url = feed.link
            title = feed.title
            pub = published_jst_date(feed) or edition_date
            category = "japan" if is_japan_related(feed) else "world"
        else:
            source = meta["meta"].split("·")[0].strip() if meta["meta"] else "Unknown"
            source_url = meta["source_url"]
            title = meta["title"]
            pub = edition_date
            category = meta["category"]
            article_id = make_article_id(
                FeedArticle(title, "", source_url, source, None),
                pub_date_jst=pub,
            )

        standard_path = legacy_dir / f"{slug}.json"
        deep_path = legacy_dir / f"{slug}.deep.json"
        if not standard_path.is_file():
            print(f"  skip missing cache {standard_path.name}")
            continue

        standard = json.loads(standard_path.read_text(encoding="utf-8"))
        deep = None
        if deep_path.is_file():
            deep = json.loads(deep_path.read_text(encoding="utf-8"))

        unified = upgrade_analysis_to_v2(standard, deep, article_id=article_id)
        unified["quality"]["generated_at"] = datetime.now(JST).isoformat(timespec="seconds")
        save_analysis(article_id, unified)

        record = ArticleRecord(
            article_id=article_id,
            edition_date=edition_date,
            source_published_date_jst=pub,
            source=source,
            source_url=source_url,
            title=title,
            slug=slug if slug.startswith(f"{rank:02d}-") else rank_slug(rank, title),
            category=category,
            selection_rank=rank,
            selection_reason="legacy_migration",
            body_clean_status="clean",
            analysis_status="complete",
        )
        records.append(record)
        article_ids.append(article_id)

    if not records:
        return None

    japan_n = sum(1 for r in records if r.category == "japan")
    world_n = sum(1 for r in records if r.category == "world")
    edition = Edition(
        edition_date=edition_date,
        status="complete",
        actual_article_count=len(records),
        source_window={"primary_date": edition_date, "fallback_days": 3},
        category_counts={"japan": japan_n, "world": world_n},
        articles=article_ids,
        article_records=records,
        generated_at=datetime.now(JST).isoformat(timespec="seconds"),
        warnings=["migrated from legacy prototype"],
    )
    save_edition(edition)
    return edition
