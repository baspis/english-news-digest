#!/usr/bin/env python3
"""Build AI-annotated English news learning pages + Anki TSV batches."""

from __future__ import annotations

import argparse
import calendar
import html
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_digest import (  # noqa: E402
    Article,
    JST,
    collect_articles,
    fmt_time,
)

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
DAYS_DIR = DIST / "days"
DATA_DIR = ROOT / "data"
ANKI_ROOT = Path.home() / "projects" / "english-anki"
OBSCURA = Path.home() / ".local" / "bin" / "obscura"
CURSOR_AGENT = Path.home() / ".local" / "bin" / "cursor-agent"
CURSOR_ENV = Path.home() / ".config" / "cursor-agent" / "env"

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")
NOISE_RE = re.compile(
    r"<|>|googletagmanager|iframe|script\b|style=|display\s*:\s*none|"
    r"Today\d|JSTToday|^\s*Image:",
    re.I,
)


@dataclass
class LearningArticle:
    day: str
    slug: str
    article: Article
    category: str
    body: str
    analysis: dict
    deep: bool = False


def today_jst() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:70] or "article"


def load_cursor_env() -> dict[str, str]:
    env = os.environ.copy()
    if CURSOR_ENV.is_file():
        for line in CURSOR_ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.startswith("export "):
                key = key[7:]
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def run_obscura(url: str, *args: str) -> str:
    cmd = [str(OBSCURA), "fetch", url, "--quiet", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "obscura failed")
    return proc.stdout.strip()


def clean_japantoday_text(raw: str) -> str:
    lines = [line.strip() for line in raw.splitlines()]
    kept: list[str] = []
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
        if re.search(r"^©", line):
            break
        if len(line) < 25 and not started:
            continue
        if line.startswith("http"):
            continue
        kept.append(line)
    return "\n".join(kept)


def fetch_article_body(url: str) -> str:
    js = (
        "Array.from(document.querySelectorAll("
        "'article p, .post p, main p, [data-component=\"text-block\"] p'"
        "))"
        ".map(p => p.textContent.trim())"
        ".filter(t => t.length > 35)"
        ".join('\\n')"
    )
    if "japantoday.com" in url:
        raw = run_obscura(url, "--eval", js)
        body = clean_japantoday_text(raw)
    else:
        body = run_obscura(url, "--eval", js)
    if len(body) < 120:
        raise RuntimeError("article body too short")
    return body


def is_valid_sentence(line: str) -> bool:
    if len(line) < 20:
        return False
    if NOISE_RE.search(line):
        return False
    if len(re.findall(r"[A-Za-z]", line)) < 8:
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


def analyze_with_ai(article: Article, body: str, sentences: list[str], *, deep: bool = False) -> dict:
    if deep:
        sentence_shape = """
    {
      "text": "exact sentence from input",
      "translation_ja": "natural Japanese translation with article context",
      "chunks": [
        {
          "text": "English chunk (meaningful phrase/clause, not single words)",
          "role_ja": "grammatical role e.g. 主語, 述語, 目的語, 修飾語, 関係詞節",
          "literal_ja": "how this chunk maps in Japanese word order",
          "note_ja": "detailed explanation: meaning, grammar, collocations, why this form"
        }
      ],
      "grammar_ja": "thorough sentence-level analysis (structure, tense, voice, clause links)",
      "deep_dive_ja": "extra depth: news style, alternatives, common learner mistakes, nuance"
    }"""
        rules = """
- Include EVERY sentence from the input list, in the same order.
- chunks: decompose each sentence into 4-10 meaningful 文節 (phrase/clause units).
  Cover the full sentence; chunk texts concatenated should reconstruct the sentence.
- role_ja: label the grammatical function clearly in Japanese.
- literal_ja: show how the chunk fits Japanese reading order (直訳寄りで可).
- note_ja: be thorough (2-4 sentences per chunk). Explain grammar, vocabulary, and news usage.
- grammar_ja: 3-6 sentences on overall sentence architecture.
- deep_dive_ja: 2-4 sentences on nuance, register, and learning tips.
- vocabulary: 6 to 10 useful words/phrases from the article.
- grammar_points: 3 to 5 article-level patterns with detailed meaning_ja."""
    else:
        sentence_shape = """
    {
      "text": "exact sentence from input",
      "translation_ja": "natural Japanese translation with article context",
      "grammar_ja": "Japanese grammar/vocabulary note for B2 learners"
    }"""
        rules = """
- Include EVERY sentence from the input list, in the same order.
- translation_ja: context-aware natural Japanese, not word-for-word.
- grammar_ja: concise notes on tense, clauses, collocations, news style.
- vocabulary: 5 to 8 useful words/phrases from the article.
- grammar_points: 2 to 4 article-level grammar patterns."""

    prompt = f"""
You are helping a Japanese B2 English learner study news.

Analyze this article and return ONLY valid JSON with this exact shape:
{{
  "summary_ja": "string, 2-3 sentences in Japanese",
  "sentences": [{sentence_shape}
  ],
  "vocabulary": [
    {{
      "word": "string",
      "pronunciation": "/IPA/",
      "meaning_ja": "Japanese",
      "example": "short English example from article or natural use",
      "example_ja": "Japanese translation of the example"
    }}
  ],
  "grammar_points": [
    {{
      "id": "short-id",
      "title": "English grammar label",
      "rule": "short English rule",
      "example": "example sentence",
      "meaning_ja": "Japanese explanation"
    }}
  ]
}}

Rules:{rules}
- Use Japanese for summary_ja, translation_ja, grammar_ja, meaning_ja, example_ja, role_ja, literal_ja, note_ja, deep_dive_ja.
- Do not wrap JSON in markdown.

Article title: {article.title}
Source: {article.source}
URL: {article.link}

Full article body for context:
{body[:6000]}

Sentences to analyze:
{json.dumps(sentences, ensure_ascii=False)}
""".strip()

    env = load_cursor_env()
    proc = subprocess.run(
        [
            str(CURSOR_AGENT),
            "-p",
            "--force",
            "--output-format",
            "json",
            prompt,
        ],
        capture_output=True,
        text=True,
        timeout=600 if deep else 300,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "cursor-agent failed")

    payload = json.loads(proc.stdout)
    raw = payload.get("result", "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def load_or_analyze(
    day: str, slug: str, article: Article, body: str, refresh: bool, *, deep: bool = False
) -> dict:
    cache_name = f"{slug}.deep.json" if deep else f"{slug}.json"
    cache = DATA_DIR / day / cache_name
    if cache.is_file() and not refresh:
        return json.loads(cache.read_text(encoding="utf-8"))

    sentences = split_sentences(body)
    if not sentences:
        raise RuntimeError("no sentences extracted")

    analysis = analyze_with_ai(article, body, sentences, deep=deep)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    return analysis


def css_block() -> str:
    return """
    :root {
      --bg: #f8f7f4;
      --surface: #ffffff;
      --ink: #1a1917;
      --muted: #6b6560;
      --line: #e8e4dc;
      --accent: #b42318;
      --accent-soft: #fdecea;
      --world: #1a4d6d;
      --world-soft: #e8f2f8;
      --translation: #2c4a3e;
      --grammar-bg: #f3f1ec;
      --today: #fff8e6;
      --today-ring: #d4a012;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      font-family: "Source Sans 3", system-ui, sans-serif;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }
    .wrap { width: min(960px, calc(100% - 2rem)); margin: 0 auto; padding: 2rem 0 4rem; }
    a { color: var(--accent); text-decoration-thickness: 1px; text-underline-offset: 2px; }
    a:hover { color: #8a1c12; }
    .topnav {
      display: flex; flex-wrap: wrap; gap: 0.5rem 1rem;
      margin-bottom: 1.25rem; font-size: 0.92rem; color: var(--muted);
    }
    .topnav a { color: var(--muted); text-decoration: none; }
    .topnav a:hover { color: var(--accent); }
    .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1rem;
    }
    h1, h2, h3 { font-family: "Fraunces", Georgia, serif; font-weight: 600; }
    h1 { font-size: clamp(1.75rem, 4vw, 2.5rem); line-height: 1.15; margin: 0 0 0.5rem; }
    h2 { font-size: 1.35rem; margin: 0 0 1rem; }
    h3 { font-size: 1.1rem; margin: 0; }
    .meta { color: var(--muted); font-size: 0.88rem; }
    .badge {
      display: inline-block; padding: 0.2rem 0.55rem; border-radius: 6px;
      font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em;
      text-transform: uppercase; margin-bottom: 0.6rem;
    }
    .badge.japan { background: var(--accent-soft); color: var(--accent); }
    .badge.world { background: var(--world-soft); color: var(--world); }
    .summary-ja {
      margin-top: 1rem; padding: 1rem 1.1rem;
      background: var(--grammar-bg); border-radius: 8px;
      border-left: 3px solid var(--accent); font-size: 0.98rem;
    }
    .sentence {
      padding: 1.1rem 0; border-bottom: 1px solid var(--line);
    }
    .sentence:last-child { border-bottom: 0; }
    .sentence .en {
      margin: 0; font-size: 1.08rem; line-height: 1.55;
      font-family: "Fraunces", Georgia, serif;
    }
    .translation-ja {
      margin: 0.55rem 0 0; color: var(--translation);
      font-size: 0.98rem; padding-left: 0.85rem;
      border-left: 2px solid #c5d9ce;
    }
    .grammar-note {
      margin-top: 0.65rem; padding: 0.75rem 0.9rem;
      background: var(--grammar-bg); border-radius: 8px;
      font-size: 0.9rem; color: #4a4640;
    }
    .grammar-note strong { color: var(--accent); font-weight: 600; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0.75rem; }
    .vocab-card, .grammar-card {
      border: 1px solid var(--line); border-radius: 10px;
      padding: 1rem; background: var(--surface);
    }
    .vocab-head { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
    .speak-btn {
      border: 1px solid var(--line); background: var(--bg);
      border-radius: 50%; width: 2rem; height: 2rem;
      cursor: pointer; font-size: 0.85rem; line-height: 1;
      display: inline-flex; align-items: center; justify-content: center;
    }
    .speak-btn:hover { background: var(--accent-soft); border-color: var(--accent); }
    .pron { color: var(--muted); font-size: 0.85rem; margin: 0.25rem 0 0.5rem; }
    .example-en { margin: 0.5rem 0 0.2rem; font-size: 0.92rem; color: #3a3632; }
    .example-ja { margin: 0; font-size: 0.88rem; color: var(--muted); }
    .card-list article {
      padding: 1.1rem 0; border-bottom: 1px solid var(--line);
    }
    .card-list article:last-child { border-bottom: 0; }
    .card-list h3 { font-size: 1.15rem; line-height: 1.3; margin: 0.3rem 0; }
    .card-list h3 a { color: inherit; text-decoration: none; }
    .card-list h3 a:hover { color: var(--accent); }
    .card-links { font-size: 0.85rem; margin-top: 0.4rem; }
    .card-links a { margin-right: 0.8rem; }
    .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    @media (max-width: 720px) { .columns { grid-template-columns: 1fr; } }
    footer { color: var(--muted); text-align: center; font-size: 0.85rem; margin-top: 1.5rem; }
    /* Calendar */
    .cal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
    .cal-header h2 { margin: 0; }
    .cal-grid {
      display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px;
    }
    .cal-dow {
      text-align: center; font-size: 0.75rem; font-weight: 600;
      color: var(--muted); padding: 0.4rem 0; text-transform: uppercase;
    }
    .cal-cell {
      aspect-ratio: 1; display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      border-radius: 8px; font-size: 0.95rem; position: relative;
      color: var(--muted);
    }
    .cal-cell.empty { visibility: hidden; }
    .cal-cell.has-edition {
      background: var(--surface); border: 1px solid var(--line);
      color: var(--ink); font-weight: 600; cursor: pointer;
      text-decoration: none;
    }
    .cal-cell.has-edition:hover { border-color: var(--accent); background: var(--accent-soft); }
    .cal-cell.today { box-shadow: inset 0 0 0 2px var(--today-ring); background: var(--today); }
    .cal-count {
      font-size: 0.65rem; font-weight: 500; color: var(--accent);
      margin-top: 2px;
    }
    .lede { color: var(--muted); max-width: 52ch; margin: 0.5rem 0 0; }
    .chunk-table { width: 100%; border-collapse: collapse; margin: 0.75rem 0; font-size: 0.9rem; }
    .chunk-table th, .chunk-table td {
      border: 1px solid var(--line); padding: 0.55rem 0.65rem;
      text-align: left; vertical-align: top;
    }
    .chunk-table th { background: var(--grammar-bg); font-weight: 600; font-size: 0.8rem; color: var(--muted); }
    .chunk-table .chunk-en { font-family: "Fraunces", Georgia, serif; font-weight: 500; white-space: nowrap; }
    .chunk-table .chunk-role { color: var(--accent); font-weight: 600; font-size: 0.82rem; white-space: nowrap; }
    .deep-dive {
      margin-top: 0.65rem; padding: 0.85rem 1rem; border-radius: 8px;
      background: #eef3f8; border-left: 3px solid var(--world); font-size: 0.9rem;
    }
    .deep-dive strong { color: var(--world); }
    .mode-badge {
      display: inline-block; margin-left: 0.5rem; padding: 0.15rem 0.5rem;
      border-radius: 6px; background: #eef3f8; color: var(--world);
      font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; vertical-align: middle;
    }
    """


def js_block() -> str:
    return """
    function speakWord(btn) {
      const word = btn.dataset.word;
      if (!word || !window.speechSynthesis) return;
      const u = new SpeechSynthesisUtterance(word);
      u.lang = 'en-US';
      u.rate = 0.9;
      speechSynthesis.cancel();
      speechSynthesis.speak(u);
    }
    """


def page_shell(title: str, body_html: str, *, with_speech: bool = False) -> str:
    script = f"<script>{js_block()}</script>" if with_speech else ""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Source+Sans+3:wght@400;500;600&display=swap" rel="stylesheet">
  <style>{css_block()}</style>
</head>
<body>
  <div class="wrap">
    {body_html}
  </div>
  {script}
</body>
</html>
"""


def render_chunks_table(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    rows = []
    for ch in chunks:
        rows.append(
            f"<tr>"
            f"<td class='chunk-en'>{html.escape(ch.get('text', ''))}</td>"
            f"<td class='chunk-role'>{html.escape(ch.get('role_ja', ''))}</td>"
            f"<td>{html.escape(ch.get('literal_ja', ''))}</td>"
            f"<td>{html.escape(ch.get('note_ja', ''))}</td>"
            f"</tr>"
        )
    return f"""
    <table class="chunk-table">
      <thead><tr>
        <th>文節</th><th>役割</th><th>直訳</th><th>解説</th>
      </tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """


def render_article_page(item: LearningArticle, *, deep: bool = False) -> str:
    a = item.article
    analysis = item.analysis
    meta = " · ".join(x for x in [a.source, fmt_time(a.published)] if x)
    day_url = f"../../days/{item.day}.html"
    mode_badge = '<span class="mode-badge">DETAILED</span>' if deep else ""

    sentences_html = []
    for idx, sent in enumerate(analysis.get("sentences", []), start=1):
        chunks_html = render_chunks_table(sent.get("chunks", [])) if deep else ""
        deep_dive = sent.get("deep_dive_ja", "")
        deep_html = (
            f'<div class="deep-dive"><strong>深掘り:</strong> {html.escape(deep_dive)}</div>'
            if deep and deep_dive
            else ""
        )
        sentences_html.append(
            f"""
            <div class="sentence" id="s{idx}">
              <p class="en">{html.escape(sent.get('text', ''))}</p>
              {chunks_html}
              <p class="translation-ja">{html.escape(sent.get('translation_ja', ''))}</p>
              <div class="grammar-note"><strong>文法:</strong> {html.escape(sent.get('grammar_ja', ''))}</div>
              {deep_html}
            </div>
            """
        )

    vocab_html = []
    for vocab in analysis.get("vocabulary", []):
        word = vocab.get("word", "")
        vocab_html.append(
            f"""
            <div class="vocab-card">
              <div class="vocab-head">
                <h3>{html.escape(word)}</h3>
                <button type="button" class="speak-btn" data-word="{html.escape(word, quote=True)}"
                        onclick="speakWord(this)" aria-label="発音を再生">&#9654;</button>
              </div>
              <div class="pron">{html.escape(vocab.get('pronunciation', ''))}</div>
              <p>{html.escape(vocab.get('meaning_ja', ''))}</p>
              <p class="example-en"><em>{html.escape(vocab.get('example', ''))}</em></p>
              <p class="example-ja">{html.escape(vocab.get('example_ja', ''))}</p>
            </div>
            """
        )

    grammar_html = []
    for gp in analysis.get("grammar_points", []):
        grammar_html.append(
            f"""
            <div class="grammar-card">
              <h3>{html.escape(gp.get('title', ''))}</h3>
              <p>{html.escape(gp.get('rule', ''))}</p>
              <p class="example-en"><em>{html.escape(gp.get('example', ''))}</em></p>
              <p>{html.escape(gp.get('meaning_ja', ''))}</p>
            </div>
            """
        )

    body = f"""
    <nav class="topnav">
      <a href="../../index.html">カレンダー</a>
      <a href="{html.escape(day_url)}">{html.escape(item.day)}</a>
      <a href="{html.escape(a.link, quote=True)}" target="_blank" rel="noopener">元記事 ↗</a>
    </nav>
    <header class="panel">
      <span class="badge {html.escape(item.category)}">{html.escape(item.category)}</span>
      <h1>{html.escape(a.title)}</h1>
      <div class="meta">{html.escape(meta)}</div>
      <div class="summary-ja">{html.escape(analysis.get('summary_ja', ''))}</div>
    </header>

    <section class="panel">
      <h2>文ごとの解説{mode_badge}</h2>
      {''.join(sentences_html)}
    </section>

    <section class="panel">
      <h2>Vocabulary</h2>
      <div class="grid">{''.join(vocab_html)}</div>
    </section>

    <section class="panel">
      <h2>Grammar focus</h2>
      <div class="grid">{''.join(grammar_html)}</div>
    </section>

    <footer>English News Learning · {html.escape(item.day)}</footer>
    """
    return page_shell(a.title, body, with_speech=True)


def render_day_page(items: list[LearningArticle], day: str, generated: str) -> str:
    japan = [i for i in items if i.category == "japan"]
    world = [i for i in items if i.category == "world"]
    dt = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=JST)
    weekday = "月火水木金土日"[dt.weekday()]
    label = f"{dt.year}年{dt.month}月{dt.day}日（{weekday}）"

    def section_block(title: str, badge: str, rows: list[LearningArticle]) -> str:
        if not rows:
            return f"<section class='panel'><h2>{html.escape(title)}</h2><p class='meta'>該当記事なし</p></section>"
        cards = []
        for item in rows:
            suffix = ".deep" if item.deep else ""
            art_url = f"../articles/{day}/{item.slug}{suffix}.html"
            vocab_n = len(item.analysis.get("vocabulary", []))
            sent_n = len(item.analysis.get("sentences", []))
            detail = ' <span class="mode-badge">DETAILED</span>' if item.deep else ""
            deep_path = DIST / "articles" / day / f"{item.slug}.deep.html"
            deep_link = ""
            if not item.deep and deep_path.is_file():
                deep_url = f"../articles/{day}/{item.slug}.deep.html"
                deep_link = f'<a href="{html.escape(deep_url)}">文節解説（詳細版）</a>'
            cards.append(
                f"""
                <article>
                  <div class="meta">{html.escape(item.article.source)} · {sent_n}文 · {vocab_n}語{detail}</div>
                  <h3><a href="{html.escape(art_url)}">{html.escape(item.article.title)}</a></h3>
                  <p>{html.escape(item.analysis.get('summary_ja', ''))}</p>
                  <div class="card-links">
                    <a href="{html.escape(art_url)}">学習ページ</a>
                    {deep_link}
                    <a href="{html.escape(item.article.link, quote=True)}" target="_blank" rel="noopener">元記事 ↗</a>
                  </div>
                </article>
                """
            )
        return f"""
        <section class="panel">
          <h2>{html.escape(title)} <span class="badge {badge}">{badge}</span></h2>
          <div class="card-list">{''.join(cards)}</div>
        </section>
        """

    body = f"""
    <nav class="topnav"><a href="../index.html">← カレンダー</a></nav>
    <header class="panel">
      <h1>{html.escape(label)}</h1>
      <p class="meta">生成: {html.escape(generated)} · {len(items)} 記事</p>
      <p class="lede">各記事を文ごとに解説。語彙・文法は Anki にもエクスポートできます。</p>
    </header>
    <div class="columns">
      {section_block("Japan & Asia", "japan", japan)}
      {section_block("World", "world", world)}
    </div>
    <footer>English News Learning Digest</footer>
    """
    return page_shell(f"{day} — News Digest", body)


def load_calendar_manifest() -> dict:
    path = DIST / "calendar.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"editions": []}


def update_calendar_manifest(day: str, items: list[LearningArticle]) -> dict:
    data = load_calendar_manifest()
    japan_n = sum(1 for i in items if i.category == "japan")
    world_n = sum(1 for i in items if i.category == "world")
    entry = {
        "date": day,
        "article_count": len(items),
        "japan_count": japan_n,
        "world_count": world_n,
        "url": f"days/{day}.html",
    }
    data["editions"] = [e for e in data.get("editions", []) if e.get("date") != day]
    data["editions"].append(entry)
    data["editions"].sort(key=lambda e: e.get("date", ""), reverse=True)
    return data


def render_calendar(manifest: dict, focus_day: str) -> str:
    dt = datetime.strptime(focus_day, "%Y-%m-%d").replace(tzinfo=JST)
    year, month = dt.year, dt.month
    editions = {e["date"]: e for e in manifest.get("editions", [])}
    today = today_jst()

    cal = calendar.Calendar(firstweekday=6)  # Sunday start
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
            if date_str in editions:
                ed = editions[date_str]
                classes.append("has-edition")
                cells.append(
                    f'<a class="{" ".join(classes)}" href="days/{html.escape(date_str)}.html">'
                    f'{day_num}<span class="cal-count">{ed["article_count"]}件</span></a>'
                )
            else:
                cells.append(f'<div class="{" ".join(classes)}">{day_num}</div>')

    body = f"""
    <header class="panel">
      <h1>English News Learning</h1>
      <p class="lede">日付を選んで、その日のニュース記事を文ごとに学習できます。</p>
    </header>
    <section class="panel">
      <div class="cal-header">
        <h2>{year}年{month_names[month]}</h2>
      </div>
      <div class="cal-grid">{''.join(cells)}</div>
    </section>
    <footer>Rebuild: <code>python3 build_learning.py</code></footer>
    """
    return page_shell("English News Learning", body)


def write_anki_tsv(items: list[LearningArticle], day: str) -> tuple[Path, Path]:
    vocab_path = ANKI_ROOT / "materials" / "news-digest" / "batches" / f"{day}-vocabulary.tsv"
    grammar_path = ANKI_ROOT / "materials" / "news-digest" / "batches" / f"{day}-grammar.tsv"
    vocab_path.parent.mkdir(parents=True, exist_ok=True)

    vocab_lines = ["word\tpronunciation\tmeaning\texample\tunit\tnote"]
    grammar_lines = ["id\ttitle\trule\texample\tmeaning\tunit\tnote"]

    for item in items:
        slug = item.slug
        for vocab in item.analysis.get("vocabulary", []):
            word = vocab.get("word", "").strip()
            if not word:
                continue
            example_ja = vocab.get("example_ja", "")
            note = f"news:{slug}"
            if example_ja:
                note = f"{note} | {example_ja}"
            row = [
                word,
                vocab.get("pronunciation", ""),
                vocab.get("meaning_ja", ""),
                vocab.get("example", ""),
                day,
                note,
            ]
            vocab_lines.append("\t".join(row))

        for gp in item.analysis.get("grammar_points", []):
            gid = f"{slug}-{gp.get('id', 'gp')}"
            row = [
                gid,
                gp.get("title", ""),
                gp.get("rule", ""),
                gp.get("example", ""),
                gp.get("meaning_ja", ""),
                day,
                item.article.title,
            ]
            grammar_lines.append("\t".join(row))

    vocab_path.write_text("\n".join(vocab_lines) + "\n", encoding="utf-8")
    grammar_path.write_text("\n".join(grammar_lines) + "\n", encoding="utf-8")
    return vocab_path, grammar_path


def import_anki(day: str) -> None:
    script = ANKI_ROOT / "scripts" / "import.py"
    for material, batch in [
        ("news-digest-vocabulary", f"{day}-vocabulary.tsv"),
        ("news-digest-grammar", f"{day}-grammar.tsv"),
    ]:
        subprocess.run(
            ["python3", str(script), material, "--batch", batch],
            cwd=ANKI_ROOT,
            check=False,
        )


def build_items(day: str, limit: int | None, refresh: bool, *, deep: bool = False) -> list[LearningArticle]:
    japan, world = collect_articles(today_only=True)
    selected: list[tuple[str, Article]] = []
    for article in japan:
        selected.append(("japan", article))
    for article in world:
        selected.append(("world", article))
    if limit is not None:
        selected = selected[:limit]

    if not selected:
        print(f"No articles published today (JST: {day}).")
        return []

    items: list[LearningArticle] = []
    for idx, (category, article) in enumerate(selected, start=1):
        base_slug = slugify(article.title)
        slug = f"{idx:02d}-{base_slug}"
        print(f"[{idx}/{len(selected)}] {article.title}")
        try:
            body = fetch_article_body(article.link)
        except Exception as exc:  # noqa: BLE001
            print(f"  skip fetch: {exc}")
            continue
        mode = "deep analyze" if deep else "analyze"
        print(f"  {mode} ({len(body)} chars)...", flush=True)
        try:
            analysis = load_or_analyze(day, slug, article, body, refresh=refresh, deep=deep)
        except Exception as exc:  # noqa: BLE001
            print(f"  skip analyze: {exc}", flush=True)
            continue
        items.append(LearningArticle(day, slug, article, category, body, analysis, deep=deep))
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Build AI learning news digest")
    parser.add_argument("--limit", type=int, help="limit number of articles")
    parser.add_argument("--refresh", action="store_true", help="ignore cached AI analysis")
    parser.add_argument("--import-anki", action="store_true", help="import generated TSV into Anki")
    parser.add_argument(
        "--deep",
        action="store_true",
        help="chunk-by-chunk detailed analysis (separate cache, slower)",
    )
    parser.add_argument(
        "--deep-only",
        action="store_true",
        help="with --deep: only write article page; keep existing day/calendar/anki",
    )
    args = parser.parse_args()

    if not OBSCURA.is_file():
        print(f"Obscura not found: {OBSCURA}")
        return 1
    if not CURSOR_AGENT.is_file():
        print(f"cursor-agent not found: {CURSOR_AGENT}")
        return 1

    day = today_jst()
    items = build_items(day, args.limit, args.refresh, deep=args.deep)
    if not items:
        return 1

    generated = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    articles_dir = DIST / "articles" / day
    articles_dir.mkdir(parents=True, exist_ok=True)
    DAYS_DIR.mkdir(parents=True, exist_ok=True)

    for item in items:
        suffix = ".deep" if args.deep else ""
        out = articles_dir / f"{item.slug}{suffix}.html"
        out.write_text(render_article_page(item, deep=args.deep), encoding="utf-8")
        print(f"  wrote {out}", flush=True)

    if not (args.deep and args.deep_only):
        day_path = DAYS_DIR / f"{day}.html"
        day_path.write_text(render_day_page(items, day, generated), encoding="utf-8")
        print(f"Wrote {day_path}", flush=True)

        manifest = update_calendar_manifest(day, items)
        manifest_path = DIST / "calendar.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        index_path = DIST / "index.html"
        index_path.write_text(render_calendar(manifest, day), encoding="utf-8")
        print(f"Wrote {index_path}", flush=True)

        vocab_path, grammar_path = write_anki_tsv(items, day)
        print(f"Wrote {vocab_path}", flush=True)
        print(f"Wrote {grammar_path}", flush=True)

        if args.import_anki:
            import_anki(day)

    print(f"Done: {len(items)} articles for {day}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
