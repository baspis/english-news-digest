"""CLI commands for the edition pipeline."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from .analyze import analyze_edition, load_analysis
from .comments import fetch_due_comments
from .anki import import_anki, write_anki_tsv
from .feeds import cache_raw_feed, fetch_all_feeds, load_cached_feed
from .migrate import migrate_legacy_edition
from .paths import BUILD_LOGS_DIR, CURSOR_AGENT, OBSCURA
from .publish import publish_edition, rebuild_calendar
from .schemas import BuildLog, Edition
from .select import load_edition, save_edition, select_edition

JST = ZoneInfo("Asia/Tokyo")


def today_jst() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")


def load_analyses_for_edition(edition: Edition) -> dict[str, dict]:
    analyses: dict[str, dict] = {}
    for record in edition.article_records:
        data = load_analysis(record.article_id)
        if data:
            analyses[record.article_id] = data
            record.analysis_status = "complete"
    return analyses


def write_build_log(log: BuildLog) -> None:
    BUILD_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    path = BUILD_LOGS_DIR / f"{log.edition_date}.json"
    path.write_text(json.dumps(log.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_build_edition(args: argparse.Namespace) -> int:
    edition_date = args.date or today_jst()
    log = BuildLog(
        edition_date=edition_date,
        started_at=datetime.now(JST).isoformat(timespec="seconds"),
        stage_counts={},
    )

    edition = load_edition(edition_date)
    if edition is None:
        edition = migrate_legacy_edition(edition_date)

    if edition is None or args.reselect:
        print(f"Selecting edition for {edition_date}...")
        raw = fetch_all_feeds()
        cache_raw_feed(edition_date, raw)
        log.stage_counts["fetched"] = len(raw)
        edition = select_edition(edition_date, reselect=args.reselect, raw_articles=raw)
        log.stage_counts["selected"] = edition.actual_article_count
    else:
        cached = load_cached_feed(edition_date)
        log.stage_counts["fetched"] = len(cached) if cached else 0
        log.stage_counts["selected"] = edition.actual_article_count

    if edition.status == "failed":
        log.errors.append("selection could not produce five articles")
        log.finished_at = datetime.now(JST).isoformat(timespec="seconds")
        write_build_log(log)
        print(f"Edition {edition_date} failed: insufficient candidates")
        return 1

    analyses = load_analyses_for_edition(edition)
    missing = [
        r for r in edition.article_records if r.article_id not in analyses
    ]
    if missing and not args.skip_analyze:
        if not OBSCURA.is_file():
            print(f"Obscura not found: {OBSCURA}")
            return 1
        if not CURSOR_AGENT.is_file():
            print(f"cursor-agent not found: {CURSOR_AGENT}")
            return 1
        print(f"Analyzing {len(missing)} articles...")
        edition, new_analyses = analyze_edition(
            edition,
            refresh=args.refresh_analysis,
            skip_ai=False,
        )
        analyses.update(new_analyses)
        log.stage_counts["analyzed"] = sum(
            1 for r in edition.article_records if r.analysis_status == "complete"
        )
    else:
        log.stage_counts["analyzed"] = len(analyses)

    complete_analyses = sum(
        1 for r in edition.article_records if r.article_id in analyses
    )
    if complete_analyses < edition.target_article_count:
        edition.status = "selected"
        save_edition(edition)
        log.errors.append(
            f"only {complete_analyses}/{edition.target_article_count} analyses complete"
        )
        log.finished_at = datetime.now(JST).isoformat(timespec="seconds")
        write_build_log(log)
        print("Edition not complete: missing analyses")
        return 1

    if not args.skip_render:
        print("Rendering...")
        publish_edition(edition, analyses, update_calendar=True)
        log.stage_counts["rendered"] = edition.actual_article_count
        save_edition(edition)

    if not args.skip_anki:
        try:
            vocab_path, grammar_path = write_anki_tsv(edition, analyses)
            print(f"Wrote {vocab_path}")
            print(f"Wrote {grammar_path}")
        except Exception as exc:  # noqa: BLE001
            edition.warnings.append(f"anki export failed: {exc}")
            log.warnings.append(str(exc))

    if args.import_anki:
        import_anki(edition_date)

    log.finished_at = datetime.now(JST).isoformat(timespec="seconds")
    log.warnings.extend(edition.warnings)
    write_build_log(log)
    print(f"Done: edition {edition_date} ({edition.status})")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    edition_date = args.date or today_jst()
    edition = load_edition(edition_date)
    if edition is None:
        edition = migrate_legacy_edition(edition_date)
    if edition is None:
        print(f"No edition data for {edition_date}")
        return 1

    analyses = load_analyses_for_edition(edition)
    if len(analyses) < edition.actual_article_count:
        print(f"Missing analyses: {len(analyses)}/{edition.actual_article_count}")
        return 1

    publish_edition(edition, analyses, update_calendar=not args.no_calendar)
    edition.status = "complete"
    save_edition(edition)
    print(f"Rendered edition {edition_date}")
    return 0


def cmd_export_anki(args: argparse.Namespace) -> int:
    edition_date = args.date or today_jst()
    edition = load_edition(edition_date)
    if edition is None:
        print(f"No edition for {edition_date}")
        return 1
    analyses = load_analyses_for_edition(edition)
    vocab_path, grammar_path = write_anki_tsv(edition, analyses)
    print(f"Wrote {vocab_path}")
    print(f"Wrote {grammar_path}")
    return 0


def cmd_import_anki(args: argparse.Namespace) -> int:
    import_anki(args.date or today_jst())
    return 0


def cmd_rebuild_calendar(args: argparse.Namespace) -> int:
    rebuild_calendar(args.date)
    print("Rebuilt calendar")
    return 0


def cmd_fetch_comments(args: argparse.Namespace) -> int:
    result = fetch_due_comments(args.date, force=args.force)
    updated: list[str] = result["updated_editions"]

    if updated:
        for edition_date in updated:
            edition = load_edition(edition_date)
            if edition is None:
                continue
            analyses = load_analyses_for_edition(edition)
            if len(analyses) < edition.actual_article_count:
                print(f"Skip render {edition_date}: missing analyses")
                continue
            print(f"Rendering {edition_date} after comment fetch...")
            publish_edition(edition, analyses, update_calendar=False)
        rebuild_calendar(updated[-1])
        print(
            f"Fetched comments for {result['fetched_articles']} articles "
            f"across {len(updated)} edition(s)"
        )
    else:
        print("No comments due for fetch")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="English News Digest edition pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build-edition", help="fetch, select, analyze, render, export")
    build.add_argument("--date", help="edition date YYYY-MM-DD (default: today JST)")
    build.add_argument("--reselect", action="store_true", help="re-run article selection")
    build.add_argument("--refresh-analysis", action="store_true", help="re-run AI analysis")
    build.add_argument("--skip-analyze", action="store_true", help="use cached analysis only")
    build.add_argument("--skip-render", action="store_true")
    build.add_argument("--skip-anki", action="store_true")
    build.add_argument("--import-anki", action="store_true")
    build.set_defaults(func=cmd_build_edition)

    render = sub.add_parser("render", help="render HTML from edition cache")
    render.add_argument("--date")
    render.add_argument("--no-calendar", action="store_true")
    render.set_defaults(func=cmd_render)

    export = sub.add_parser("export-anki", help="export Anki TSV for edition")
    export.add_argument("--date")
    export.set_defaults(func=cmd_export_anki)

    imp = sub.add_parser("import-anki", help="import TSV into Anki")
    imp.add_argument("--date")
    imp.set_defaults(func=cmd_import_anki)

    cal = sub.add_parser("rebuild-calendar", help="rebuild calendar index and index.html")
    cal.add_argument("--date", help="focus month from this date")
    cal.set_defaults(func=cmd_rebuild_calendar)

    comments = sub.add_parser(
        "fetch-comments",
        help="fetch JT popular comments once per article (24h after edition build)",
    )
    comments.add_argument("--date", help="only process this edition date")
    comments.add_argument("--force", action="store_true", help="dev only: ignore final/eligible gates")
    comments.set_defaults(func=cmd_fetch_comments)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
