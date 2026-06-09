#!/usr/bin/env python3
"""Build a daily English news digest HTML page."""

from __future__ import annotations

import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist" / "index.html"

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
    r"imperial family|yen|fukushima|tsunami|hokkaido|shinkansen|narita|haneda)\b",
    re.I,
)

@dataclass
class Article:
    title: str
    summary: str
    link: str
    source: str
    published: datetime | None

    @property
    def key(self) -> str:
        return re.sub(r"\W+", "", self.title.lower())[:120]


def fetch_rss(url: str, source: str, limit: int = 12) -> list[Article]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "english-news-digest/1.0 (+local)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()

    root = ET.fromstring(raw)
    channel = root.find("channel")
    if channel is None:
        return []

    items: list[Article] = []
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
        items.append(Article(title, summary, link, source, published))
    return items


def _text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return re.sub(r"\s+", " ", node.text).strip()


def is_japan_related(article: Article) -> bool:
    if article.source.startswith("Japan Today"):
        return True
    return bool(JAPAN_RE.search(f"{article.title} {article.summary}"))


def dedupe(articles: list[Article]) -> list[Article]:
    seen: set[str] = set()
    out: list[Article] = []
    for article in articles:
        if article.key in seen:
            continue
        seen.add(article.key)
        out.append(article)
    return out


def sort_articles(articles: list[Article]) -> list[Article]:
    return sorted(
        articles,
        key=lambda a: a.published or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )


def is_published_today_jst(article: Article) -> bool:
    if not article.published:
        return False
    today = datetime.now(JST).date()
    return article.published.astimezone(JST).date() == today


def collect_articles(today_only: bool = False) -> tuple[list[Article], list[Article]]:
    all_items: list[Article] = []
    for source, url in FEEDS.items():
        try:
            all_items.extend(fetch_rss(url, source))
        except Exception as exc:  # noqa: BLE001 - show source errors in HTML
            all_items.append(
                Article(
                    title=f"Failed to fetch {source}",
                    summary=str(exc),
                    link=url,
                    source=source,
                    published=None,
                )
            )

    japan_pool = dedupe([a for a in all_items if is_japan_related(a)])
    world_pool = dedupe([a for a in all_items if not is_japan_related(a)])

    if today_only:
        japan_pool = [a for a in japan_pool if is_published_today_jst(a)]
        world_pool = [a for a in world_pool if is_published_today_jst(a)]

    def score_japan(article: Article) -> tuple[int, datetime]:
        priority = 0
        if article.source.startswith("Japan Today"):
            priority += 2
        if JAPAN_RE.search(f"{article.title} {article.summary}"):
            priority += 1
        return (priority, article.published or datetime.min.replace(tzinfo=timezone.utc))

    japan = sorted(japan_pool, key=score_japan, reverse=True)[:8]
    world = sort_articles(world_pool)[:8]
    return japan, world


def fmt_time(dt: datetime | None) -> str:
    if not dt:
        return ""
    local = dt.astimezone()
    return local.strftime("%Y-%m-%d %H:%M")


def render_article(article: Article) -> str:
    summary = html.escape(article.summary)
    if len(summary) > 260:
        summary = summary[:257] + "..."
    meta = " · ".join(x for x in [article.source, fmt_time(article.published)] if x)
    return f"""
    <article class="card">
      <div class="card-meta">{html.escape(meta)}</div>
      <h3><a href="{html.escape(article.link, quote=True)}" target="_blank" rel="noopener">{html.escape(article.title)}</a></h3>
      <p>{summary}</p>
    </article>
    """


def render_page(japan: list[Article], world: list[Article]) -> str:
    generated = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    japan_html = "\n".join(render_article(a) for a in japan) or "<p class='empty'>No articles found.</p>"
    world_html = "\n".join(render_article(a) for a in world) or "<p class='empty'>No articles found.</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>English News Digest</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@8..72,500;8..72,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #f4f1ea;
      --paper: #fffdf8;
      --ink: #1d1c1a;
      --muted: #5f5a52;
      --line: #ddd4c4;
      --accent: #9b2c2c;
      --accent-soft: #f3e3df;
      --world: #1f4d63;
      --world-soft: #e4eef3;
      --shadow: 0 18px 50px rgba(29, 28, 26, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #efe5d2 0, transparent 28rem),
        linear-gradient(180deg, #f7f3ec 0%, var(--bg) 100%);
      font-family: "IBM Plex Sans", sans-serif;
      line-height: 1.6;
    }}
    .wrap {{
      width: min(1100px, calc(100% - 2rem));
      margin: 0 auto;
      padding: 2.5rem 0 4rem;
    }}
    header {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 2rem 2.2rem;
      box-shadow: var(--shadow);
      margin-bottom: 1.5rem;
    }}
    .eyebrow {{
      color: var(--accent);
      font-size: 0.82rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      font-weight: 600;
      margin: 0 0 0.6rem;
    }}
    h1 {{
      font-family: "Newsreader", Georgia, serif;
      font-size: clamp(2.2rem, 5vw, 3.6rem);
      line-height: 1.05;
      margin: 0 0 0.8rem;
      font-weight: 700;
    }}
    .lede {{
      margin: 0;
      color: var(--muted);
      max-width: 62ch;
      font-size: 1.02rem;
    }}
    .meta-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.8rem 1.2rem;
      margin-top: 1.2rem;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1.2rem;
    }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
    section {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 1.3rem;
      box-shadow: var(--shadow);
    }}
    .section-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 1rem;
      padding-bottom: 0.8rem;
      border-bottom: 1px solid var(--line);
    }}
    .section-head h2 {{
      margin: 0;
      font-family: "Newsreader", Georgia, serif;
      font-size: 1.7rem;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 0.35rem 0.7rem;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .badge.japan {{ background: var(--accent-soft); color: var(--accent); }}
    .badge.world {{ background: var(--world-soft); color: var(--world); }}
    .card {{
      padding: 1rem 0;
      border-bottom: 1px solid rgba(93, 90, 82, 0.12);
    }}
    .card:last-child {{ border-bottom: 0; padding-bottom: 0; }}
    .card-meta {{
      color: var(--muted);
      font-size: 0.82rem;
      margin-bottom: 0.35rem;
    }}
    .card h3 {{
      margin: 0 0 0.45rem;
      font-family: "Newsreader", Georgia, serif;
      font-size: 1.22rem;
      line-height: 1.25;
      font-weight: 700;
    }}
    .card h3 a {{
      color: inherit;
      text-decoration: none;
    }}
    .card h3 a:hover {{ color: var(--accent); }}
    .card p {{
      margin: 0;
      color: #403c37;
      font-size: 0.96rem;
    }}
    .empty {{
      color: var(--muted);
      margin: 0.5rem 0 0;
    }}
    footer {{
      margin-top: 1.2rem;
      color: var(--muted);
      font-size: 0.88rem;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <p class="eyebrow">Daily Reading</p>
      <h1>English News Digest</h1>
      <p class="lede">Japan-focused headlines first, then major international stories from BBC and Guardian. Built for B2 reading practice.</p>
      <div class="meta-bar">
        <span>Generated: {html.escape(generated)}</span>
        <span>Sources: Japan Today, BBC, Guardian</span>
        <span>{len(japan)} Japan-related · {len(world)} World</span>
      </div>
    </header>

    <div class="grid">
      <section>
        <div class="section-head">
          <h2>Japan &amp; Asia</h2>
          <span class="badge japan">Primary</span>
        </div>
        {japan_html}
      </section>

      <section>
        <div class="section-head">
          <h2>World</h2>
          <span class="badge world">International</span>
        </div>
        {world_html}
      </section>
    </div>

    <footer>
      Regenerate with <code>python3 build_digest.py</code> in <code>~/projects/english-news-digest</code>
    </footer>
  </div>
</body>
</html>
"""


def main() -> int:
    japan, world = collect_articles()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render_page(japan, world), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Japan-related: {len(japan)} | World: {len(world)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
