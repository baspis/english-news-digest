"""RSS fetch and source definitions."""

from __future__ import annotations

import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from .paths import RAW_FEED_DIR
from .schemas import FeedArticle

JST = ZoneInfo("Asia/Tokyo")

FEEDS = {
    "Japan Today National": "https://japantoday.com/category/national/feed",
    "Japan Today Crime": "https://japantoday.com/category/crime/feed",
    "Japan Today Business": "https://japantoday.com/category/business/feed",
    "BBC Asia": "https://feeds.bbci.co.uk/news/world/asia/rss.xml",
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC Top": "https://feeds.bbci.co.uk/news/rss.xml",
    "Guardian World": "https://www.theguardian.com/world/rss",
}

JAPAN_RE = re.compile(
    r"\b(japan|japanese|tokyo|osaka|kyoto|yokohama|nagoya|sapporo|fukuoka|"
    r"okinawa|hokkaido|hiroshima|kobe|sendai|ishiba|liberal democratic party|"
    r"imperial family|yen|fukushima|tsunami|shinkansen|narita|haneda)\b",
    re.I,
)


def _text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return re.sub(r"\s+", " ", node.text).strip()


def fetch_rss(url: str, source: str, limit: int = 12) -> list[FeedArticle]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "english-news-digest/2.0 (+local)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()

    root = ET.fromstring(raw)
    channel = root.find("channel")
    if channel is None:
        return []

    items: list[FeedArticle] = []
    for item in channel.findall("item")[:limit]:
        title = _text(item.find("title"))
        summary = _text(item.find("description"))
        link = _text(item.find("link"))
        pub = _text(item.find("pubDate"))
        published = None
        if pub:
            try:
                published = parsedate_to_datetime(pub).astimezone(timezone.utc)
            except (TypeError, ValueError, OverflowError):
                published = None
        if not title or not link:
            continue
        items.append(FeedArticle(title, summary, link, source, published))
    return items


def fetch_all_feeds(limit_per_feed: int = 12) -> list[FeedArticle]:
    all_items: list[FeedArticle] = []
    for source, url in FEEDS.items():
        try:
            all_items.extend(fetch_rss(url, source, limit=limit_per_feed))
        except Exception as exc:  # noqa: BLE001
            print(f"  feed warning {source}: {exc}")
    return all_items


def cache_raw_feed(edition_date: str, articles: list[FeedArticle]) -> None:
    RAW_FEED_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_FEED_DIR / f"{edition_date}.json"
    payload = [
        {
            "title": a.title,
            "summary": a.summary,
            "link": a.link,
            "source": a.source,
            "published": a.published.isoformat() if a.published else None,
        }
        for a in articles
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cached_feed(edition_date: str) -> list[FeedArticle] | None:
    path = RAW_FEED_DIR / f"{edition_date}.json"
    if not path.is_file():
        return None
    items: list[FeedArticle] = []
    for row in json.loads(path.read_text(encoding="utf-8")):
        published = None
        if row.get("published"):
            published = datetime.fromisoformat(row["published"])
        items.append(
            FeedArticle(
                row["title"],
                row["summary"],
                row["link"],
                row["source"],
                published,
            )
        )
    return items


def is_japan_related(article: FeedArticle) -> bool:
    if article.source.startswith("Japan Today"):
        return True
    return bool(JAPAN_RE.search(f"{article.title} {article.summary}"))


def published_jst_date(article: FeedArticle) -> str | None:
    if not article.published:
        return None
    return article.published.astimezone(JST).strftime("%Y-%m-%d")
