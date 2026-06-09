# English News Digest — 再設計用資材パッケージ

作成日: 2026-06-09

この Zip は、英語ニュース学習アプリ `english-news-digest` をゼロベース再設計するための判断材料一式です。

## 最初に読むファイル

| 順 | ファイル | 内容 |
|----|----------|------|
| 1 | `HANDOFF_BRIEF.md` | 設計 LLM への引き継ぎブリーフ（依頼文・未決事項・成功基準） |
| 2 | `PROMPT_FOR_DESIGN_LLM.txt` | そのまま貼れる起動プロンプト |
| 3 | `CURRENT_STATE.md` | 2026-06-09 時点のプロトタイプ状態スナップショット |
| 4 | `KNOWN_ISSUES.md` | 既知の問題と実測メモ |

## ディレクトリ構成

```
redesign-handoff/
├── README.md                          # このファイル
├── HANDOFF_BRIEF.md                   # 引き継ぎブリーフ全文
├── PROMPT_FOR_DESIGN_LLM.txt          # コピペ用プロンプト
├── CURRENT_STATE.md                   # 現状サマリ
├── KNOWN_ISSUES.md                    # 既知の問題
├── context/
│   ├── english-project-overview.md    # 英語学習プロジェクト概要（抜粋）
│   └── english-execution-spec.md      # 実行仕様（抜粋）
├── prototype/
│   ├── build_digest.py                # 見出しダイジェスト（現行）
│   └── build_learning.py              # 学習ビルダー（現行・再設計対象）
├── samples/
│   ├── data/                          # AI 解析 JSON サンプル
│   ├── dist/                          # 生成 HTML サンプル
│   └── anki/                          # Anki TSV + materials.json
└── notes/
    └── build-performance.md           # ビルド時間・コストの目安
```

## 設計 LLM への渡し方

1. この Zip を解凍する（またはフォルダごとアップロード）
2. `PROMPT_FOR_DESIGN_LLM.txt` の内容を最初のメッセージとして送る
3. 必要に応じて `HANDOFF_BRIEF.md` と `prototype/` を参照させる

## ローカルでの元プロジェクト

```
~/projects/english-news-digest/
~/projects/english-anki/
```
