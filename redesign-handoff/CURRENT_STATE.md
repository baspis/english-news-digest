# 現状スナップショット（2026-06-09）

## プロジェクト概要

- **場所**: `~/projects/english-news-digest/`
- **目的**: 無料英語ニュース（Japan Today / BBC / Guardian）を B2 学習者向けに収集・解説
- **出力**: 静的 HTML + JSON キャッシュ + Anki TSV

## スクリプト

| ファイル | 役割 |
|----------|------|
| `build_digest.py` | RSS から見出しダイジェスト（2カラム: Japan / World、各最大8件） |
| `build_learning.py` | 本文取得 → AI 解説 → カレンダー/日次/記事 HTML + Anki TSV |

## 現行の画面構成（不完全）

```
dist/index.html              # カレンダー（トップ）
dist/days/2026-06-09.html    # 日次一覧
dist/articles/2026-06-09/    # 記事詳細
```

ナビゲーションの骨格はあるが、**「1日=5件」が設計の軸になっていない**。

## 2026-06-09 の実データ

| 項目 | 数 |
|------|-----|
| JST 今日公開の RSS 記事（フィルタ前） | 約16件 |
| `data/2026-06-09/*.json`（AI キャッシュ） | 9件 |
| `dist/articles/2026-06-09/*.html`（通常版） | 5件 |
| `dist/articles/2026-06-09/*.deep.html` | 1件 |
| `calendar.json` の article_count | 5（japan 5 / world 0） |

途中ビルド（`--limit 5`）で止まった状態。キャッシュは9件あるが HTML は5件のみ。

## RSS ソース（build_digest.py）

```python
FEEDS = {
    "Japan Today National": "https://japantoday.com/category/national/feed",
    "Japan Today Crime": "https://japantoday.com/category/crime/feed",
    "Japan Today Business": "https://japantoday.com/category/business/feed",
    "BBC Asia": "https://feeds.bbci.co.uk/news/world/asia/rss.xml",
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC Top": "https://feeds.bbci.co.uk/news/rss.xml",
    "Guardian World": "https://www.theguardian.com/world/rss",
}
```

## 記事選定ロジック（現行）

1. 全フィードから取得（各12件上限）
2. Japan / World に分類（Japan Today は基本 Japan、キーワードマッチ）
3. `today_only=True` のとき JST 公開日でフィルタ
4. Japan 最大8 + World 最大8（**5件固定ではない**）
5. `build_learning.py --limit N` でさらに切る

## 技術依存

| ツール | パス | 用途 |
|--------|------|------|
| Obscura | `~/.local/bin/obscura` | 記事本文の JS レンダリング取得 |
| cursor-agent | `~/.local/bin/cursor-agent` | AI 解析（デフォルト composer-2.5） |
| english-anki | `~/projects/english-anki/` | TSV → AnkiConnect import |

## 現行コマンド

```bash
python3 build_digest.py
python3 build_learning.py [--limit N] [--refresh] [--deep] [--deep-only] [--import-anki]
```

## ユーザーが再設計で変えたいこと

- **大上段の設計から作り直す**
- UX を **カレンダー → 5件一覧 → 詳細** に統一
- 日次エディション（Edition）を中心概念にする
