"""cursor-agent prompts and analysis cache."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .clean import fetch_article_body, load_body, save_body, split_sentences
from .paths import ANALYSES_DIR, CURSOR_AGENT, CURSOR_ENV
from .schemas import (
    SCHEMA_VERSION,
    ArticleRecord,
    Edition,
    validate_analysis,
)

JST = ZoneInfo("Asia/Tokyo")


def analysis_cache_path(article_id: str) -> Path:
    safe_id = article_id.replace(":", "__")
    return ANALYSES_DIR / f"{safe_id}.json"


def load_analysis(article_id: str) -> dict | None:
    path = analysis_cache_path(article_id)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def save_analysis(article_id: str, data: dict) -> None:
    path = analysis_cache_path(article_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_suffix(".json.bak")
    if path.is_file():
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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


def analyze_with_ai(
    title: str,
    source: str,
    url: str,
    body: str,
    sentences: list[str],
) -> dict:
    sentence_shape = """
    {
      "text": "exact sentence from input",
      "translation_ja": "natural Japanese translation with article context",
      "grammar_ja": "Japanese grammar/vocabulary note for B2 learners",
      "chunks": [
        {
          "text": "English chunk (meaningful phrase/clause)",
          "role_ja": "grammatical role e.g. 主語, 述語",
          "literal_ja": "how this chunk maps in Japanese word order",
          "note_ja": "explanation: meaning, grammar, collocations"
        }
      ],
      "deep_dive_ja": "extra depth: news style, alternatives, learner mistakes",
      "difficulty": "easy|medium|hard"
    }"""

    prompt = f"""
You are helping a Japanese B2 English learner study news.

Analyze this article and return ONLY valid JSON with this exact shape:
{{
  "summary_ja": "string, 2-3 sentences in Japanese",
  "reading_level": "B2",
  "sentences": [{sentence_shape}
  ],
  "vocabulary": [
    {{
      "word": "string",
      "pronunciation": "/IPA/",
      "meaning_ja": "Japanese",
      "example": "short English example from article or natural use",
      "example_ja": "Japanese translation of the example",
      "source_sentence_id": "s001"
    }}
  ],
  "grammar_points": [
    {{
      "id": "short-stable-id",
      "title": "English grammar label",
      "rule": "short English rule",
      "example": "example sentence",
      "meaning_ja": "Japanese explanation"
    }}
  ]
}}

Rules:
- Include EVERY sentence from the input list, in the same order.
- translation_ja: context-aware natural Japanese, not word-for-word.
- grammar_ja: concise notes on tense, clauses, collocations, news style.
- chunks: optional per sentence; include 3-8 chunks when the sentence is non-trivial.
- deep_dive_ja: optional; 1-3 sentences when useful.
- vocabulary: 5 to 8 useful words/phrases from the article.
- vocabulary word: use the clearest headword for learners. Prefer collocations over bare ambiguous words (e.g. "castle keep" not "keep"; "opt for" not "opt"). If a common verb/noun homograph exists, include enough context in word and meaning_ja (e.g. meaning_ja: "（城の）天守閣 ※動詞 keep（保つ）とは別").
- vocabulary example: must make the target word's part of speech obvious when read alone. Do NOT clip a fragment that looks like a different reading (bad: "the castle keeps long cherished" reads as verb keeps; good: "closed the castle keeps" or "Hiroshima Castle's reconstructed keep"). Include a verb, determiner, or possessive when needed so noun vs verb is unambiguous.
- grammar_points: 2 to 4 article-level grammar patterns.
- Use Japanese for summary_ja, translation_ja, grammar_ja, meaning_ja, example_ja, role_ja, literal_ja, note_ja, deep_dive_ja.
- Do not wrap JSON in markdown.

Article title: {title}
Source: {source}
URL: {url}

Full article body for context:
{body[:6000]}

Sentences to analyze:
{json.dumps(sentences, ensure_ascii=False)}
""".strip()

    env = load_cursor_env()
    proc = subprocess.run(
        [str(CURSOR_AGENT), "-p", "--force", "--output-format", "json", prompt],
        capture_output=True,
        text=True,
        timeout=600,
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

    for idx, sent in enumerate(data.get("sentences", []), start=1):
        sent.setdefault("sentence_id", f"s{idx:03d}")
        sent.setdefault("chunks", [])
        sent.setdefault("deep_dive_ja", "")
        sent.setdefault("difficulty", "medium")

    data["schema_version"] = SCHEMA_VERSION
    data["analysis_level"] = "standard_with_deep_chunks"
    data["quality"] = {
        "sentence_count": len(data.get("sentences", [])),
        "noise_flags": [],
        "ai_model": "cursor-agent",
        "generated_at": datetime.now(JST).isoformat(timespec="seconds"),
    }
    return data


def ensure_body(record: ArticleRecord) -> tuple[str, str, list[str]]:
    cached = load_body(record.article_id)
    if cached:
        return cached, record.body_clean_status, []
    body, status, warnings = fetch_article_body(record.source_url)
    save_body(record.article_id, body)
    return body, status, warnings


def analyze_article(
    record: ArticleRecord,
    *,
    refresh: bool = False,
    skip_ai: bool = False,
) -> dict:
    cached = load_analysis(record.article_id)
    if cached and not refresh:
        errors = validate_analysis(cached)
        if not errors:
            return cached

    body, status, _ = ensure_body(record)
    record.body_clean_status = status
    sentences = split_sentences(body)
    if not sentences:
        raise RuntimeError("no sentences extracted")

    if skip_ai and cached:
        return cached

    analysis = analyze_with_ai(
        record.title,
        record.source,
        record.source_url,
        body,
        sentences,
    )
    analysis["article_id"] = record.article_id
    errors = validate_analysis(analysis)
    if errors:
        raise RuntimeError(f"analysis validation failed: {errors}")

    save_analysis(record.article_id, analysis)
    record.analysis_status = "complete"
    return analysis


def analyze_edition(
    edition: Edition,
    *,
    refresh: bool = False,
    skip_ai: bool = False,
) -> tuple[Edition, dict[str, dict]]:
    analyses: dict[str, dict] = {}
    for record in edition.article_records:
        print(f"  analyze [{record.selection_rank}/5] {record.title[:60]}...")
        try:
            analysis = analyze_article(record, refresh=refresh, skip_ai=skip_ai)
            analyses[record.article_id] = analysis
        except Exception as exc:  # noqa: BLE001
            record.analysis_status = "failed"
            edition.warnings.append(f"analysis failed {record.article_id}: {exc}")
            print(f"    failed: {exc}")

    complete = sum(1 for r in edition.article_records if r.analysis_status == "complete")
    if complete == edition.target_article_count:
        edition.status = "selected"
    elif complete < edition.target_article_count:
        edition.status = "selected"
    return edition, analyses
