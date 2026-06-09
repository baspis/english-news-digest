# English News Digest

Daily English news reader for B2 learners. One edition per day, five articles, sentence-by-sentence study notes.

**Live site:** https://baspis.github.io/english-news-digest/

## Quick start

```bash
python3 -m english_news_digest build-edition --date 2026-06-09
python3 -m english_news_digest render --date 2026-06-09
./scripts/deploy-pages.sh
```

## Commands

```bash
python3 -m english_news_digest build-edition [--date YYYY-MM-DD] [--reselect] [--refresh-analysis]
python3 -m english_news_digest render [--date YYYY-MM-DD]
python3 -m english_news_digest fetch-comments [--date YYYY-MM-DD]
python3 -m english_news_digest export-anki [--date YYYY-MM-DD]
python3 -m english_news_digest rebuild-calendar
```

## Two-phase pipeline

| Phase | When | What |
|-------|------|------|
| A | Daily ~07:00 JST | `build-edition` — full article analysis + render + deploy |
| B | Hourly | `fetch-comments` — JT only, 24h after edition build, **once per article** |

Comments are Popular top 5 (or fewer if not available). After the first fetch, status is `final` and never refreshed.

## Deploy (GitHub Pages)

Static HTML in `docs/`, served from `main`.

```bash
./scripts/deploy-pages.sh
```

## Automation (systemd timers on llm-devbox)

```bash
./scripts/install-timers.sh
```

| Timer | Schedule | Script |
|-------|----------|--------|
| `english-news-digest-build.timer` | Daily 07:00 JST | `scripts/run-build.sh` |
| `english-news-digest-comments.timer` | Every hour | `scripts/run-comments.sh` |

Logs: `~/logs/english-news-digest/build.log` and `comments.log`

Manual runs:

```bash
./scripts/run-build.sh
./scripts/run-comments.sh
```
