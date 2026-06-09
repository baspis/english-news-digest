"""URL/title normalization, article_id, dedupe."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from .feeds import FeedArticle, published_jst_date
from .schemas import FeedArticle as _  # noqa: F401 - re-export context

SOURCE_PREFIX = {
    "Japan Today": "japantoday",
    "BBC": "bbc",
    "Guardian": "guardian",
}


def slugify(title: str, max_len: int = 70) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:max_len] or "article"


def source_prefix(source: str) -> str:
    for key, prefix in SOURCE_PREFIX.items():
        if source.startswith(key):
            return prefix
    return re.sub(r"[^a-z0-9]+", "", source.lower())[:20] or "unknown"


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    query = parse_qs(parsed.query, keep_blank_values=False)
    for key in list(query):
        if key.lower().startswith("utm_") or key in {"fbclid", "ref"}:
            del query[key]
    clean_query = urlencode({k: v[0] for k, v in query.items()}, doseq=False)
    path = parsed.path.rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc.lower(), path, "", clean_query, ""))


def normalize_title(title: str) -> str:
    return re.sub(r"\W+", "", title.lower())[:120]


def make_article_id(article: FeedArticle, pub_date_jst: str | None = None) -> str:
    date = pub_date_jst or published_jst_date(article) or "unknown"
    slug = slugify(article.title, max_len=40)
    return f"{source_prefix(article.source)}:{date}:{slug}"


def dedupe_articles(articles: list[FeedArticle]) -> list[FeedArticle]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    out: list[FeedArticle] = []
    for article in articles:
        url_key = normalize_url(article.link)
        title_key = normalize_title(article.title)
        if url_key in seen_urls or title_key in seen_titles:
            continue
        seen_urls.add(url_key)
        seen_titles.add(title_key)
        out.append(article)
    return out


def rank_slug(selection_rank: int, title: str) -> str:
    return f"{selection_rank:02d}-{slugify(title)}"


def fmt_time(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.astimezone().strftime("%Y-%m-%d %H:%M")
