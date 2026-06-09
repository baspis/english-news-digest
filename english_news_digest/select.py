"""Edition selection, scoring, five-article guarantee."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .feeds import JST, FeedArticle, is_japan_related, published_jst_date
from .normalize import dedupe_articles, make_article_id, rank_slug
from .paths import EDITIONS_DIR
from .schemas import (
    FALLBACK_DAYS,
    JAPAN_TARGET,
    SELECTION_POLICY,
    TARGET_ARTICLE_COUNT,
    WORLD_TARGET,
    ArticleRecord,
    Edition,
)

SOURCE_PRIORITY = {
    "Japan Today National": 4,
    "Japan Today Crime": 4,
    "Japan Today Business": 3,
    "BBC Asia": 4,
    "BBC World": 3,
    "BBC Top": 2,
    "Guardian World": 2,
}


def edition_path(edition_date: str) -> Path:
    return EDITIONS_DIR / edition_date / "edition.json"


def load_edition(edition_date: str) -> Edition | None:
    path = edition_path(edition_date)
    if not path.is_file():
        return None
    return Edition.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_edition(edition: Edition) -> None:
    path = edition_path(edition.edition_date)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(edition.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_assigned_article_ids(exclude_date: str | None = None) -> set[str]:
    assigned: set[str] = set()
    if not EDITIONS_DIR.is_dir():
        return assigned
    for edition_dir in EDITIONS_DIR.iterdir():
        if not edition_dir.is_dir():
            continue
        if exclude_date and edition_dir.name == exclude_date:
            continue
        ed_path = edition_dir / "edition.json"
        if not ed_path.is_file():
            continue
        data = json.loads(ed_path.read_text(encoding="utf-8"))
        if data.get("status") == "complete":
            assigned.update(data.get("articles", []))
    return assigned


def score_candidate(
    article: FeedArticle,
    category: str,
    edition_date: str,
    body_len: int = 0,
) -> float:
    score = float(SOURCE_PRIORITY.get(article.source, 1))
    if category == "japan" and article.source.startswith("Japan Today"):
        score += 2
    if category == "world" and article.source.startswith("BBC"):
        score += 1.5
    pub = published_jst_date(article)
    if pub == edition_date:
        score += 3
    elif pub:
        try:
            days = (
                datetime.strptime(edition_date, "%Y-%m-%d")
                - datetime.strptime(pub, "%Y-%m-%d")
            ).days
            if 0 < days <= FALLBACK_DAYS:
                score += max(0, 2 - days * 0.5)
        except ValueError:
            pass
    title = article.title
    if len(title) > 100:
        score -= 1
    if body_len > 6000:
        score -= 2
    elif body_len > 4000:
        score -= 1
    if "Failed to fetch" in article.title:
        score -= 100
    return score


@dataclass
class ScoredCandidate:
    article: FeedArticle
    category: str
    article_id: str
    score: float
    pool: str
    body_clean_status: str = "clean"


def build_candidate_pools(
    all_articles: list[FeedArticle],
    edition_date: str,
    assigned: set[str],
) -> tuple[list[ScoredCandidate], list[ScoredCandidate]]:
    edition_dt = datetime.strptime(edition_date, "%Y-%m-%d").replace(tzinfo=JST)
    fallback_start = (edition_dt - timedelta(days=FALLBACK_DAYS)).date()

    primary_japan: list[ScoredCandidate] = []
    primary_world: list[ScoredCandidate] = []
    fallback_japan: list[ScoredCandidate] = []
    fallback_world: list[ScoredCandidate] = []

    for article in dedupe_articles(all_articles):
        article_id = make_article_id(article)
        if article_id in assigned:
            continue
        pub = published_jst_date(article)
        if not pub:
            continue
        try:
            pub_date = datetime.strptime(pub, "%Y-%m-%d").date()
        except ValueError:
            continue

        category = "japan" if is_japan_related(article) else "world"
        sc = score_candidate(article, category, edition_date)

        if pub == edition_date:
            pool = "primary"
            target = primary_japan if category == "japan" else primary_world
        elif fallback_start <= pub_date < edition_dt.date():
            pool = "fallback"
            target = fallback_japan if category == "japan" else fallback_world
        else:
            continue

        target.append(
            ScoredCandidate(article, category, article_id, sc, pool)
        )

    for pool in (primary_japan, primary_world, fallback_japan, fallback_world):
        pool.sort(key=lambda c: c.score, reverse=True)

    primary = primary_japan + primary_world
    fallback = fallback_japan + fallback_world
    return primary, fallback


def pick_balanced_five(
    primary: list[ScoredCandidate],
    fallback: list[ScoredCandidate],
) -> list[ScoredCandidate]:
    selected: list[ScoredCandidate] = []
    used_ids: set[str] = set()

    def take_from(pool: list[ScoredCandidate], category: str, n: int) -> None:
        for cand in pool:
            if len([s for s in selected if s.category == category]) >= n:
                break
            if cand.category != category or cand.article_id in used_ids:
                continue
            selected.append(cand)
            used_ids.add(cand.article_id)

    japan_primary = [c for c in primary if c.category == "japan"]
    world_primary = [c for c in primary if c.category == "world"]
    japan_all = japan_primary + [c for c in fallback if c.category == "japan"]
    world_all = world_primary + [c for c in fallback if c.category == "world"]

    take_from(japan_all, "japan", JAPAN_TARGET)
    take_from(world_all, "world", WORLD_TARGET)

    remaining = [c for c in primary + fallback if c.article_id not in used_ids]
    remaining.sort(key=lambda c: c.score, reverse=True)
    while len(selected) < TARGET_ARTICLE_COUNT and remaining:
        cand = remaining.pop(0)
        if cand.article_id not in used_ids:
            selected.append(cand)
            used_ids.add(cand.article_id)

    return selected[:TARGET_ARTICLE_COUNT]


def select_edition(
    edition_date: str,
    *,
    reselect: bool = False,
    raw_articles: list[FeedArticle] | None = None,
) -> Edition:
    existing = load_edition(edition_date)
    if existing and existing.status == "complete" and not reselect:
        return existing

    if reselect and existing:
        prev = edition_path(edition_date)
        backup = edition_path(edition_date).with_name("edition.previous.json")
        backup.write_text(prev.read_text(encoding="utf-8"), encoding="utf-8")

    articles = raw_articles
    if articles is None:
        articles = fetch_all_feeds()
    assigned = list_assigned_article_ids(exclude_date=edition_date if reselect else None)
    primary, fallback = build_candidate_pools(articles, edition_date, assigned)
    picked = pick_balanced_five(primary, fallback)

    japan_n = sum(1 for c in picked if c.category == "japan")
    world_n = sum(1 for c in picked if c.category == "world")
    status = "selected" if len(picked) == TARGET_ARTICLE_COUNT else "draft"
    if len(picked) < TARGET_ARTICLE_COUNT:
        status = "failed"

    records: list[ArticleRecord] = []
    article_ids: list[str] = []
    for rank, cand in enumerate(picked, start=1):
        pub = published_jst_date(cand.article) or edition_date
        reason = f"{cand.category}_{cand.pool}_recent"
        slug = rank_slug(rank, cand.article.title)
        rec = ArticleRecord(
            article_id=cand.article_id,
            edition_date=edition_date,
            source_published_date_jst=pub,
            source=cand.article.source,
            source_url=cand.article.link,
            title=cand.article.title,
            slug=slug,
            category=cand.category,
            selection_rank=rank,
            selection_reason=reason,
            body_clean_status=cand.body_clean_status,
            analysis_status="pending",
        )
        records.append(rec)
        article_ids.append(cand.article_id)

    edition = Edition(
        edition_date=edition_date,
        status=status,
        actual_article_count=len(picked),
        source_window={"primary_date": edition_date, "fallback_days": FALLBACK_DAYS},
        category_counts={"japan": japan_n, "world": world_n},
        articles=article_ids,
        article_records=records,
        generated_at=datetime.now(JST).isoformat(timespec="seconds"),
        warnings=[],
    )
    if len(picked) < TARGET_ARTICLE_COUNT:
        edition.warnings.append(
            f"only {len(picked)} candidates in {FALLBACK_DAYS}-day fallback window"
        )
    save_edition(edition)
    return edition
