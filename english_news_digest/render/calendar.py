"""Calendar screen renderer."""

from __future__ import annotations

import calendar
import html
from datetime import datetime
from zoneinfo import ZoneInfo

from .assets import page_shell

JST = ZoneInfo("Asia/Tokyo")


def today_jst() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")


def render_calendar_page(calendar_index: dict, focus_day: str) -> str:
    dt = datetime.strptime(focus_day, "%Y-%m-%d").replace(tzinfo=JST)
    year, month = dt.year, dt.month
    editions = calendar_index.get("editions", {})
    today = today_jst()

    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)

    month_names = [
        "", "1月", "2月", "3月", "4月", "5月", "6月",
        "7月", "8月", "9月", "10月", "11月", "12月",
    ]

    cells = []
    for dow in ["日", "月", "火", "水", "木", "金", "土"]:
        cells.append(f'<div class="cal-dow">{dow}</div>')

    for week in weeks:
        for day_num in week:
            if day_num == 0:
                cells.append('<div class="cal-cell empty"></div>')
                continue
            date_str = f"{year:04d}-{month:02d}-{day_num:02d}"
            classes = ["cal-cell"]
            if date_str == today:
                classes.append("today")
            if date_str in editions and editions[date_str].get("status") == "complete":
                ed = editions[date_str]
                classes.append("has-edition")
                href = ed.get("path", f"editions/{date_str}/index.html")
                cells.append(
                    f'<a class="{" ".join(classes)}" href="{html.escape(href)}" '
                    f'aria-label="{date_str} edition, {ed.get("article_count", 5)} articles">'
                    f'{day_num}<span class="cal-count">{ed.get("article_count", 5)}</span></a>'
                )
            else:
                cells.append(f'<div class="{" ".join(classes)}">{day_num}</div>')

    body = f"""
    <header class="panel page-header">
      <h1>English News Digest</h1>
      <p class="lede">Choose a daily edition.</p>
    </header>
    <section class="panel">
      <div class="cal-header">
        <h2>{year}年{month_names[month]}</h2>
      </div>
      <div class="cal-grid">{''.join(cells)}</div>
    </section>
    <footer>English News Digest</footer>
    """
    return page_shell("English News Digest", body, assets_prefix="assets")
