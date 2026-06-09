# 既知の問題・実測メモ

## 1. 記事数が不安定

- `collect_articles(today_only=True)` は「今日 JST 公開の全件」を返す
- 2026-06-09 は16件あったが、ビルドは `--limit 5` で5件に制限
- カレンダー・日次ページの件数が日によってバラバラになる設計

## 2. 通常版と深掘り版の二重構造

- `--deep` で別 JSON（`*.deep.json`）・別 HTML（`*.deep.html`）
- 日次ページに「文節解説（詳細版）」リンクが別途出現
- ユーザーは2種類のページの存在を意識する必要がある

## 3. Japan Today 本文ノイズ

`data/2026-06-09/01-memorial-service-....json` の後半に、記事本文ではない文が混入:

- イベント告知（TWO ROOMS NIHOMBASHI）
- Facebook ログイン案内
- ニュースアラート登録案内

原因: `clean_japantoday_text()` が記事末尾の広告・フッターを十分に除去できていない。

## 4. ビルド速度

| 工程 | 1記事あたり目安 |
|------|----------------|
| RSS 取得 | 全体で約1秒 |
| Obscura（本文） | 約6秒 |
| cursor-agent（通常解析） | 約1〜3分 |
| cursor-agent（深掘り解析） | 約2〜4分 |

16件を `--refresh` で直列処理すると15〜30分以上かかる。  
BBC 長文（50文超）は1件だけで数分。

## 5. キャッシュと表示の不整合

- `data/` に解析済み JSON があっても `dist/` に HTML がないことがある
- 途中失敗・limit 変更で状態がずれる
- idempotent な「edition 完成」概念がない

## 6. build_learning.py の責務過多（890行）

1ファイルに以下が全部入っている:

- 本文取得・クリーニング
- AI プロンプト・解析
- HTML レンダリング（カレンダー/日次/記事）
- カレンダーマニフェスト
- Anki TSV 生成・import

## 7. 旧 dist 構造の残骸

`dist/articles/` 直下に日付なしの旧 HTML（01〜15）が残存。  
新構造は `dist/articles/2026-06-09/` 配下。

## 8. World 記事が0件の日がある

2026-06-09 の calendar.json: japan_count=5, world_count=0。  
JST フィルタ後に Japan Today 中心になりやすい。

## 9. AI コスト

- cursor-agent + composer-2.5（Cursor Team 枠）
- 深掘り5本/日 ≈ 8〜12万 tokens/日（推定）
- 正確なトークン数は API レスポンスに含まれない

## 10. 深掘り1件の実測（2026-06-09）

記事: Memorial service（Japan Today、14文）

| 版 | JSON サイズ | 生成時間 |
|----|------------|----------|
| 通常 | 11 KB | 約1〜2分 |
| 深掘り | 33 KB | 約3分 |
