"""Japan Today reader comments: fetch Popular top N and annotate for study."""

from __future__ import annotations

import html
import json
import re
import subprocess
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

from .analyze import load_cursor_env
from .paths import CURSOR_AGENT, DATA

JST = ZoneInfo("Asia/Tokyo")
COMMENTS_DIR = DATA / "comments" / "v2"
USER_AGENT = "english-news-digest/2.0 (+local)"
MIN_COMMENT_CHARS = 12


class _CommentTextParser(HTMLParser):
  def __init__(self) -> None:
    super().__init__()
    self.parts: list[str] = []

  def handle_data(self, data: str) -> None:
    text = data.strip()
    if text:
      self.parts.append(text)

  def text(self) -> str:
    return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def comment_cache_path(article_id: str) -> Path:
  safe_id = article_id.replace(":", "__")
  return COMMENTS_DIR / f"{safe_id}.json"


def load_comments(article_id: str) -> dict | None:
  path = comment_cache_path(article_id)
  if path.is_file():
    return json.loads(path.read_text(encoding="utf-8"))
  return None


def save_comments(article_id: str, data: dict) -> Path:
  path = comment_cache_path(article_id)
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
  return path


def _fetch_url(url: str, *, xhr: bool = False) -> str:
  headers = {"User-Agent": USER_AGENT}
  if xhr:
    headers["X-Requested-With"] = "XMLHttpRequest"
  req = urllib.request.Request(url, headers=headers)
  with urllib.request.urlopen(req, timeout=30) as resp:
    return resp.read().decode("utf-8", errors="replace")


def extract_jt_article_id(page_html: str) -> int | None:
  match = re.search(r'id="comments-js"[^>]*data-json="([^"]+)"', page_html)
  if not match:
    return None
  payload = json.loads(html.unescape(match.group(1)))
  popular_route = payload.get("route", {}).get("popular", "")
  id_match = re.search(r"/article/(\d+)/comment", popular_route)
  return int(id_match.group(1)) if id_match else None


def html_to_comment_text(body_html: str) -> str:
  parser = _CommentTextParser()
  parser.feed(body_html)
  return parser.text()


def fetch_jt_popular_comments(source_url: str, *, limit: int = 3) -> list[dict]:
  if "japantoday.com" not in source_url:
    raise ValueError("only japantoday.com URLs are supported")

  page_html = _fetch_url(source_url)
  article_id = extract_jt_article_id(page_html)
  if article_id is None:
    raise RuntimeError("could not find Japan Today article id in page")

  api_url = f"https://japantoday.com/rest.api/article/{article_id}/comment?order=popular"
  raw = _fetch_url(api_url, xhr=True)
  payload = json.loads(raw)
  if not payload.get("success"):
    raise RuntimeError(payload.get("message", "comment API failed"))

  comments: list[dict] = []
  for entry in payload.get("comments", []):
    text = html_to_comment_text(entry.get("body", ""))
    if len(text) < MIN_COMMENT_CHARS:
      continue
    comments.append(
      {
        "comment_id": entry.get("comment_id"),
        "author": entry.get("user", {}).get("name", ""),
        "text_raw": text,
        "rating": entry.get("rating", 0),
        "positive_rating": entry.get("positive_rating", 0),
        "negative_rating": entry.get("negative_rating", 0),
        "posted_at": entry.get("date_created", ""),
      }
    )
    if len(comments) >= limit:
      break

  if not comments:
    raise RuntimeError("no comments met minimum length")

  return comments


def annotate_comments_with_ai(
  comments: list[dict],
  *,
  article_title: str,
  article_url: str,
) -> list[dict]:
  prompt = f"""
You annotate Japan Today reader comments for a Japanese B2 English learner.
Return ONLY valid JSON:
{{
  "items": [
    {{
      "rank": 1,
      "text_raw": "exact comment text from input",
      "translation_ja": "natural Japanese translation",
      "notes_ja": ["short note on ellipsis/slang/non-standard grammar", "optional second note"],
      "standard_en": "standard English rewrite when the original is non-standard or fragmentary; else empty string",
      "marked_terms": [
        {{"term": "word or phrase", "symbol": "※", "note_ja": "why mark it (rude/slang/off-limits in polite speech)"}}
      ]
    }}
  ]
}}

Rules:
- Keep text_raw exactly as given. Do NOT clean up the English.
- translation_ja: faithful, natural Japanese. Include tone (anger, sarcasm, sympathy).
- notes_ja: 1-2 bullets max. Explain native-like omissions, fragments, comma splices, spoken grammar, common "errors".
- standard_en: only when useful to contrast casual/native writing with textbook form.
- marked_terms: flag slurs, strong insults, vulgar words the learner should not use in polite contexts.
  Use symbol ※ for rude/offensive/taboo-in-polite-company terms.
  Use symbol ◇ for casual slang that is not necessarily offensive.
  If none, use [].
- Do not add content warnings or moral lectures.
- Include EVERY comment from input, same order.

Article: {article_title}
URL: {article_url}

Comments:
{json.dumps(comments, ensure_ascii=False, indent=2)}
""".strip()

  env = load_cursor_env()
  proc = subprocess.run(
    [str(CURSOR_AGENT), "-p", "--force", "--output-format", "json", prompt],
    capture_output=True,
    text=True,
    timeout=300,
    env=env,
  )
  if proc.returncode != 0:
    raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "cursor-agent failed")

  payload = json.loads(proc.stdout)
  raw = payload.get("result", "").strip()
  if raw.startswith("```"):
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
  data = json.loads(raw)

  items = data.get("items", [])
  for idx, item in enumerate(items, start=1):
    item.setdefault("rank", idx)
    item.setdefault("notes_ja", [])
    item.setdefault("standard_en", "")
    item.setdefault("marked_terms", [])
    src = comments[idx - 1] if idx - 1 < len(comments) else {}
    item.setdefault("comment_id", src.get("comment_id"))
    item.setdefault("author", src.get("author", ""))
    item.setdefault("rating", src.get("rating", 0))
    item.setdefault("posted_at", src.get("posted_at", ""))
  return items


def build_community_appendix(
  article_id: str,
  source_url: str,
  article_title: str,
  *,
  limit: int = 3,
  refresh: bool = False,
) -> dict:
  if not refresh:
    cached = load_comments(article_id)
    if cached:
      return cached

  raw_comments = fetch_jt_popular_comments(source_url, limit=limit)
  items = annotate_comments_with_ai(
    raw_comments,
    article_title=article_title,
    article_url=source_url,
  )

  appendix = {
    "article_id": article_id,
    "source": "japantoday",
    "order": "popular",
    "limit": limit,
    "fetched_at": datetime.now(JST).isoformat(timespec="seconds"),
    "items": items,
  }
  save_comments(article_id, appendix)
  return appendix


def render_community_appendix(appendix: dict | None) -> str:
  if not appendix or not appendix.get("items"):
    return ""

  import html as html_mod

  cards = []
  for item in appendix["items"]:
    notes = "".join(
      f"<li>{html_mod.escape(note)}</li>" for note in item.get("notes_ja", [])
    )
    notes_html = f"<ul class='comment-notes'>{notes}</ul>" if notes else ""

    standard = item.get("standard_en", "").strip()
    standard_html = ""
    if standard:
      standard_html = (
        f"<p class='comment-standard'><span class='label'>標準形:</span> "
        f"{html_mod.escape(standard)}</p>"
      )

    marks = []
    for mark in item.get("marked_terms", []):
      sym = mark.get("symbol", "※")
      term = mark.get("term", "")
      note = mark.get("note_ja", "")
      marks.append(
        f"<li><span class='mark-symbol'>{html_mod.escape(sym)}</span> "
        f"<strong>{html_mod.escape(term)}</strong> — {html_mod.escape(note)}</li>"
      )
    marks_html = ""
    if marks:
      marks_html = f"<ul class='comment-marks'>{''.join(marks)}</ul>"

    rating = item.get("rating", 0)
    author = item.get("author", "")
    cards.append(
      f"""
      <article class="comment-card">
        <div class="comment-meta">#{item.get('rank', 0)} · {html_mod.escape(author)}
          · score {rating}</div>
        <p class="comment-raw">{html_mod.escape(item.get('text_raw', ''))}</p>
        <p class="comment-translation">{html_mod.escape(item.get('translation_ja', ''))}</p>
        {notes_html}
        {standard_html}
        {marks_html}
      </article>
      """
    )

  return f"""
  <section class="panel comment-appendix">
    <details open>
      <summary>Reader reactions（Popular Top 3）</summary>
      <p class="comment-legend">※ 丁寧な場では避ける語　◇ くだけたスラング</p>
      {''.join(cards)}
    </details>
  </section>
  """
