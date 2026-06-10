"""Daily article list renderer."""

from __future__ import annotations

import html
from datetime import datetime
from zoneinfo import ZoneInfo

from ..comments import comment_reaction_label, edition_comments_summary, is_japan_today
from ..schemas import Edition
from .assets import page_shell
from .speech import speak_button

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
    category_summary = ", ".join(
        f"{name} {edition.category_counts[name]}"
        for name in sorted(edition.category_counts)
    ) or "no categories"
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
        rank_comments = ""
        if record.selection_reason.startswith("jt_comments_"):
            n = record.selection_reason.removeprefix("jt_comments_")
            rank_text = f"{n} comments at selection"
            rank_comments = (
                f'<span class="meta">{html.escape(rank_text)}</span>'
                f"{speak_button(rank_text, compact=True)}"
            )

        rows.append(
            f"""
            <li class="article-row">
              <div class="rank">{record.selection_rank:02d}</div>
              <div>
                <div class="row-top speak-line">
                  <span class="badge {html.escape(record.category)}">{html.escape(record.category)}</span>
                  {speak_button(record.category, compact=True)}
                  <span class="meta">{html.escape(record.source)}</span>
                  {speak_button(record.source, compact=True)}
                  <span class="meta">{sent_n} sentences · {vocab_n} vocabulary</span>
                  {speak_button(f"{sent_n} sentences {vocab_n} vocabulary", compact=True)}
                  {rank_comments}
                  {reactions_html}
                </div>
                <h2 class="card-title speak-line">
                  <a href="{art_url}">{html.escape(record.title)}</a>
                  {speak_button(record.title, compact=True)}
                </h2>
                <p class="summary">{html.escape(analysis.get('summary_ja', ''))}</p>
                <div class="row-actions speak-line">
                  {f'<span class="meta">{html.escape(source_date)}</span>{speak_button(source_date, compact=True)}' if source_date else ''}
                  <a href="{art_url}">Open article</a>
                  {speak_button("Open article", compact=True)}
                  <a class="secondary" href="{html.escape(record.source_url, quote=True)}" target="_blank" rel="noopener">Original ↗</a>
                  {speak_button("Original", compact=True)}
                </div>
              </div>
            </li>
            """
        )

    lede = (
        "Japan Today articles published on this date (JST): one per category "
        "(National, Crime, Business, Politics, World, Tech), chosen by reader "
        "comment count within each category."
    )
    body = f"""
    <nav class="breadcrumb speak-line" aria-label="Breadcrumb">
      <a href="../../index.html">Calendar</a>
      {speak_button("Calendar", compact=True)}
      <span class="sep">/</span>
      <span>{html.escape(edition.edition_date)}</span>
    </nav>
    <header class="panel page-header">
      <h1>{html.escape(label)}</h1>
      <p class="meta speak-line">{edition.actual_article_count} articles · {html.escape(category_summary)}{html.escape(comments_meta)} · Generated {html.escape(generated)}
        {speak_button(f"{edition.actual_article_count} articles", compact=True)}
        {speak_button(category_summary, compact=True)}
        {speak_button(f"Generated {generated}", compact=True)}</p>
      <p class="lede speak-line">{html.escape(lede)}{speak_button(lede)}</p>
    </header>
    <section class="panel">
      <ul class="edition-list">
        {''.join(rows)}
      </ul>
    </section>
    <footer class="speak-line">English News Digest · {html.escape(edition.edition_date)}
      {speak_button("English News Digest", compact=True)}</footer>
    """
    return page_shell(f"{edition.edition_date} — Daily Edition", body, assets_prefix="../../assets")
