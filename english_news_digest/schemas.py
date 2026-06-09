"""Data models and JSON schema helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

SCHEMA_VERSION = 2
TARGET_ARTICLE_COUNT = 5
SELECTION_POLICY = "balanced-five-fill-with-recent-unassigned"
FALLBACK_DAYS = 3
JAPAN_TARGET = 3
WORLD_TARGET = 2


@dataclass
class FeedArticle:
    title: str
    summary: str
    link: str
    source: str
    published: datetime | None


@dataclass
class ArticleRecord:
    article_id: str
    edition_date: str
    source_published_date_jst: str
    source: str
    source_url: str
    title: str
    slug: str
    category: str
    selection_rank: int
    selection_reason: str
    body_clean_status: str = "clean"
    analysis_status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Edition:
    edition_date: str
    status: str
    target_article_count: int = TARGET_ARTICLE_COUNT
    actual_article_count: int = 0
    selection_policy: str = SELECTION_POLICY
    source_window: dict[str, Any] = field(
        default_factory=lambda: {"primary_date": "", "fallback_days": FALLBACK_DAYS}
    )
    category_counts: dict[str, int] = field(
        default_factory=lambda: {"japan": 0, "world": 0}
    )
    articles: list[str] = field(default_factory=list)
    article_records: list[ArticleRecord] = field(default_factory=list)
    generated_at: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["article_records"] = [r.to_dict() for r in self.article_records]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Edition:
        records = [
            ArticleRecord(**r) for r in data.get("article_records", [])
        ]
        return cls(
            edition_date=data["edition_date"],
            status=data["status"],
            target_article_count=data.get("target_article_count", TARGET_ARTICLE_COUNT),
            actual_article_count=data.get("actual_article_count", 0),
            selection_policy=data.get("selection_policy", SELECTION_POLICY),
            source_window=data.get("source_window", {}),
            category_counts=data.get("category_counts", {"japan": 0, "world": 0}),
            articles=data.get("articles", []),
            article_records=records,
            generated_at=data.get("generated_at", ""),
            warnings=data.get("warnings", []),
        )


@dataclass
class BuildLog:
    edition_date: str
    started_at: str
    finished_at: str = ""
    stage_counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_analysis(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version", 1) < SCHEMA_VERSION:
        errors.append("schema_version below current")
    for key in ("summary_ja", "sentences"):
        if key not in data:
            errors.append(f"missing {key}")
    if not isinstance(data.get("sentences"), list) or not data["sentences"]:
        errors.append("sentences empty")
    return errors


def upgrade_analysis_to_v2(
    standard: dict[str, Any],
    deep: dict[str, Any] | None = None,
    article_id: str = "",
) -> dict[str, Any]:
    """Merge legacy standard + optional deep caches into unified schema v2."""
    out: dict[str, Any] = {
        "article_id": article_id,
        "schema_version": SCHEMA_VERSION,
        "analysis_level": "standard_with_deep_chunks",
        "reading_level": "B2",
        "summary_ja": standard.get("summary_ja", ""),
        "sentences": [],
        "vocabulary": standard.get("vocabulary", []),
        "grammar_points": standard.get("grammar_points", []),
        "quality": {
            "sentence_count": len(standard.get("sentences", [])),
            "noise_flags": [],
            "ai_model": "cursor-agent",
            "generated_at": "",
        },
    }
    deep_by_text: dict[str, dict[str, Any]] = {}
    if deep:
        for sent in deep.get("sentences", []):
            text = sent.get("text", "")
            if text:
                deep_by_text[text] = sent

    sentences: list[dict[str, Any]] = []
    for idx, sent in enumerate(standard.get("sentences", []), start=1):
        text = sent.get("text", "")
        merged = {
            "sentence_id": f"s{idx:03d}",
            "text": text,
            "translation_ja": sent.get("translation_ja", ""),
            "grammar_ja": sent.get("grammar_ja", ""),
            "chunks": [],
            "deep_dive_ja": "",
            "difficulty": "medium",
        }
        if text in deep_by_text:
            ds = deep_by_text[text]
            merged["chunks"] = ds.get("chunks", [])
            merged["deep_dive_ja"] = ds.get("deep_dive_ja", "")
            if ds.get("grammar_ja"):
                merged["grammar_ja"] = ds["grammar_ja"]
        sentences.append(merged)

    out["sentences"] = sentences
    out["quality"]["sentence_count"] = len(sentences)
    return out
