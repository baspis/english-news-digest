"""Shared HTML for Web Speech read-aloud buttons."""

from __future__ import annotations

import html


def speak_button(
    text: str,
    *,
    aria_label: str = "英文を読み上げ",
    compact: bool = False,
) -> str:
    stripped = (text or "").strip()
    if not stripped:
        return ""
    classes = "speak-btn"
    if compact:
        classes += " speak-btn--inline"
    return (
        f'<button type="button" class="{classes}" '
        f'data-text="{html.escape(stripped, quote=True)}" '
        f'onclick="speakText(this)" aria-label="{html.escape(aria_label)}">&#9654;</button>'
    )
