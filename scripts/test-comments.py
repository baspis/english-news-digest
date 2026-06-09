#!/usr/bin/env python3
"""Test Japan Today Popular comments for one article."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from english_news_digest.comments import (
    COMMENT_LIMIT,
    fetch_comments_for_record,
    fetch_jt_popular_comments,
    load_comments,
)
from english_news_digest.select import load_edition


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and annotate JT popular comments")
    parser.add_argument("--date", default="2026-06-09")
    parser.add_argument("--rank", type=int, default=1, help="article selection rank 1-5")
    parser.add_argument("--force", action="store_true", help="dev only: bypass final/eligible gates")
    parser.add_argument("--fetch-only", action="store_true", help="skip AI annotation")
    args = parser.parse_args()

    edition = load_edition(args.date)
    if edition is None:
        print(f"No edition for {args.date}", file=sys.stderr)
        return 1

    record = next((r for r in edition.article_records if r.selection_rank == args.rank), None)
    if record is None:
        print(f"No article rank {args.rank}", file=sys.stderr)
        return 1

    print(f"Article: {record.title}")
    print(f"URL: {record.source_url}\n")

    if args.fetch_only:
        comments = fetch_jt_popular_comments(record.source_url, limit=COMMENT_LIMIT)
        print(json.dumps(comments, ensure_ascii=False, indent=2))
        return 0

    appendix = fetch_comments_for_record(record, edition, force=args.force)
    if appendix is None:
        cached = load_comments(record.article_id)
        print(json.dumps(cached or {"status": "skipped"}, ensure_ascii=False, indent=2))
        return 0

    print(json.dumps(appendix, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
