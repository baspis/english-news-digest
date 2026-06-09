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
python3 -m english_news_digest export-anki [--date YYYY-MM-DD]
python3 -m english_news_digest rebuild-calendar
```

## Deploy (GitHub Pages)

Same pattern as [child-english-starter](https://baspis.github.io/child-english-starter/): static HTML in `docs/`, served from `main`.

```bash
./scripts/deploy-pages.sh
```

This syncs `dist/` → `docs/`, commits, and pushes. GitHub Pages picks it up automatically.
