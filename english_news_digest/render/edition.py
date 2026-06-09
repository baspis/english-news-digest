"""Daily article list renderer."""

from __future__ import annotations

import html
from datetime import datetime
from zoneinfo import ZoneInfo

from ..comments import comment_reaction_label, edition_comments_summary, is_japan_today
from ..schemas import Edition
from .assets import page_shell

JST = ZoneInfo("Asia/Tokyo")


def _format_source_date(pub: str, edition_date: str) -> str:
    if pub == edition_date:
        return ""
    try:
        dt = datetime.strptime(pub, "%Y-%m-%d")
        return f"Source date {dt.strftime('%b')} {dt.day}"
    except ValueError:
        return f"Source date {pub}"


def render_edition_page(
    edition: Edition,
    analyses: dict[str, dict],
    generated: str,
) -> str:
    dt = datetime.strptime(edition.edition_date, "%Y-%m-%d").replace(tzinfo=JST)
    weekday = "月火水木金土日"[dt.weekday()]
    label = f"{dt.year}年{dt.month}月{dt.day}日（{weekday}）"
    japan_n = edition.category_counts.get("japan", 0)
    world_n = edition.category_counts.get("world", 0)
    comments = edition_comments_summary(edition)
    comments_meta = ""
    if comments.get("comments_item_count", 0) > 0:
        comments_meta = f" · 💬 {comments['comments_item_count']} reactions"

    rows = []
    for record in edition.article_records:
        analysis = analyses.get(record.article_id, {})
        sent_n = len(analysis.get("sentences", []))
        vocab_n = len(analysis.get("vocabulary", []))
        source_date = _format_source_date(record.source_published_date_jst, edition.edition_date)
        art_url = f"articles/{html.escape(record.slug)}.html"
        reactions = comment_reaction_label(record.article_id) if is_japan_today(record) else ""
        reactions_html = f'<span class="meta">{html.escape(reactions)}</span>' if reactions else ""

        rows.append(
            f"""
            <li class="article-row">
              <div class="rank">{record.selection_rank:02d}</div>
              <div>
                <div class="row-top">
                  <span class="badge {html.escape(record.category)}">{html.escape(record.category)}</span>
                  <span class="meta">{html.escape(record.source)}</span>
                  <span class="meta">{sent_n} sentences · {vocab_n} vocabulary</span>
                  {reactions_html}
                </div>
                <h2 class="card-title"><a href="{art_url}">{html.escape(record.title)}</a></h2>
                <p class="summary">{html.escape(analysis.get('summary_ja', ''))}</p>
                <div class="row-actions">
                  {f'<span class="meta">{html.escape(source_date)}</span>' if source_date else ''}
                  <a href="{art_url}">Open article</a>
                  <a class="secondary" href="{html.escape(record.source_url, quote=True)}" target="_blank" rel="noopener">Original ↗</a>
                </div>
              </div>
            </li>
            """
        )

    body = f"""
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <a href="../../index.html">Calendar</a>
      <span class="sep">/</span>
      <span>{html.escape(edition.edition_date)}</span>
    </nav>
    <header class="panel page-header">
      <h1>{html.escape(label)}</h1>
      <p class="meta">{edition.actual_article_count} articles · Japan {japan_n} / World {world_n}{html.escape(comments_meta)} · Generated {html.escape(generated)}</p>
      <p class="lede">Today's five articles for reading and study.</p>
    </header>
    <section class="panel">
      <ul class="edition-list">
        {''.join(rows)}
      </ul>
    </section>
    <footer>English News Digest · {html.escape(edition.edition_date)}</footer>
    """
    return page_shell(f"{edition.edition_date} — Daily Edition", body, assets_prefix="../../assets")
