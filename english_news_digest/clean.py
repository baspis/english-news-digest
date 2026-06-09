"""Body extraction and source-specific cleaners."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .paths import BODIES_DIR, OBSCURA

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")
NOISE_RE = re.compile(
    r"<|>|googletagmanager|iframe|script\b|style=|display\s*:\s*none|"
    r"Today\d|JSTToday|^\s*Image:",
    re.I,
)

JAPANTODAY_STOP_PHRASES = (
    "Join us for an unforgettable evening",
    "Get your ticket now",
    "Only 50 Early Bird Tickets",
    "Use your Facebook account",
    "By doing so, you will also receive an email",
    "Comments",
    "©",
)


def run_obscura(url: str, *args: str) -> str:
    cmd = [str(OBSCURA), "fetch", url, "--quiet", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "obscura failed")
    return proc.stdout.strip()


def clean_japantoday_text(raw: str) -> tuple[str, list[str]]:
    lines = [line.strip() for line in raw.splitlines()]
    kept: list[str] = []
    warnings: list[str] = []
    started = False
    for line in lines:
        if not line or NOISE_RE.search(line):
            continue
        if line in {"TOKYO", "national", "crime", "business"}:
            started = True
            continue
        if re.search(r"Comments$", line) or re.search(r"^\d+Comments$", line):
            continue
        if re.search(r"^June \d", line):
            continue
        if any(line.startswith(p) for p in JAPANTODAY_STOP_PHRASES):
            warnings.append("japantoday_footer_noise")
            break
        if re.search(r"^©", line):
            break
        if len(line) < 25 and not started:
            continue
        if line.startswith("http"):
            continue
        kept.append(line)
    return "\n".join(kept), warnings


def fetch_article_body(url: str) -> tuple[str, str, list[str]]:
    js = (
        "Array.from(document.querySelectorAll("
        "'article p, .post p, main p, [data-component=\"text-block\"] p'"
        "))"
        ".map(p => p.textContent.trim())"
        ".filter(t => t.length > 35)"
        ".join('\\n')"
    )
    warnings: list[str] = []
    if "japantoday.com" in url:
        raw = run_obscura(url, "--eval", js)
        body, jt_warnings = clean_japantoday_text(raw)
        warnings.extend(jt_warnings)
        status = "suspect" if jt_warnings else "clean"
    else:
        body = run_obscura(url, "--eval", js)
        status = "clean"

    if len(body) < 120:
        raise RuntimeError("article body too short")
    return body, status, warnings


def body_cache_path(article_id: str) -> Path:
    safe_id = article_id.replace(":", "__")
    return BODIES_DIR / f"{safe_id}.txt"


def load_body(article_id: str) -> str | None:
    path = body_cache_path(article_id)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def save_body(article_id: str, body: str) -> None:
    path = body_cache_path(article_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def is_valid_sentence(line: str) -> bool:
    if len(line) < 20:
        return False
    if NOISE_RE.search(line):
        return False
    if len(re.findall(r"[A-Za-z]", line)) < 8:
        return False
    for phrase in JAPANTODAY_STOP_PHRASES:
        if phrase.lower() in line.lower():
            return False
    return True


def split_sentences(body: str) -> list[str]:
    chunks = [part.strip() for part in SENTENCE_SPLIT.split(body) if part.strip()]
    out: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        for line in chunk.splitlines():
            line = line.strip()
            if not is_valid_sentence(line):
                continue
            key = line.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(line)
    return out
