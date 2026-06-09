# ビルド性能・コスト目安

## パイプライン段階

```
RSS fetch → article selection → Obscura body fetch → sentence split → cursor-agent analyze → JSON cache → HTML render → Anki TSV
```

## ボトルネック

**95%以上が cursor-agent の応答待ち。** Obscura は記事あたり数秒。

## 高速化の既知手段

| 手段 | 効果 |
|------|------|
| キャッシュ再利用（`--refresh` なし） | HTML 再生成は数秒〜数分 |
| `--limit N` | 記事数を制限 |
| 深掘りは `--deep-only` で個別生成 | 日次ページを壊さない |
| 長文のプロンプト分割 | 未実装（設計課題） |
| 並列 AI 呼び出し | 未実装（レート制限に注意） |

## 深掘り運用の現実的レンジ

| パターン | 1日の AI 時間目安 |
|----------|------------------|
| 通常5件 | 5〜15分 |
| 深掘り5件 | 10〜25分 |
| 深掘り1件 + 通常4件 | 5〜10分 |

## cursor-agent 呼び出し（現行）

```python
subprocess.run([
    "cursor-agent", "-p", "--force", "--output-format", "json", prompt
], timeout=600 if deep else 300)
```

モデル未指定 → デフォルト `composer-2.5`。
