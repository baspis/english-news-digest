# English News Digest

Daily English news reader for B2 learners. One edition per day, five articles, sentence-by-sentence study notes.

## Quick start

```bash
python3 -m english_news_digest build-edition --date 2026-06-09
python3 -m english_news_digest render --date 2026-06-09
```

Open `dist/index.html` locally, or use the Tailscale URL on VPS (`https://llm-devbox/`).

## Commands

```bash
python3 -m english_news_digest build-edition [--date YYYY-MM-DD] [--reselect] [--refresh-analysis]
python3 -m english_news_digest render [--date YYYY-MM-DD]
python3 -m english_news_digest export-anki [--date YYYY-MM-DD]
python3 -m english_news_digest rebuild-calendar
```

## Deploy (VPS)

```bash
./scripts/deploy-vps.sh
```

On `llm-devbox`, static files are served from `dist/` via Tailscale Serve.
