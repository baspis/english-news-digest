"""TSV export and optional import."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .paths import ANKI_ROOT
from .schemas import ArticleRecord, Edition


def write_anki_tsv(edition: Edition, analyses: dict[str, dict]) -> tuple[Path, Path]:
    day = edition.edition_date
    vocab_path = ANKI_ROOT / "materials" / "news-digest" / "batches" / f"{day}-vocabulary.tsv"
    grammar_path = ANKI_ROOT / "materials" / "news-digest" / "batches" / f"{day}-grammar.tsv"
    vocab_path.parent.mkdir(parents=True, exist_ok=True)

    vocab_lines = ["word\tpronunciation\tmeaning\texample\tunit\tnote"]
    grammar_lines = ["id\ttitle\trule\texample\tmeaning\tunit\tnote"]
    seen_words: dict[str, int] = {}

    for record in edition.article_records:
        analysis = analyses.get(record.article_id)
        if not analysis:
            continue
        slug = record.slug

        for vocab in analysis.get("vocabulary", []):
            word = vocab.get("word", "").strip()
            if not word:
                continue
            key = word.lower()
            if key in seen_words:
                continue
            seen_words[key] = 1
            sentence_id = vocab.get("source_sentence_id", "")
            example_ja = vocab.get("example_ja", "")
            note = f"news:{slug}"
            if sentence_id:
                note = f"{note} | sentence:{sentence_id}"
            if example_ja:
                note = f"{note} | {example_ja}"
            row = [
                word,
                vocab.get("pronunciation", ""),
                vocab.get("meaning_ja", ""),
                vocab.get("example", ""),
                day,
                note,
            ]
            vocab_lines.append("\t".join(row))

        for gp in analysis.get("grammar_points", []):
            gid = gp.get("id", "gp")
            if not gid.startswith(slug):
                gid = f"{slug}-{gid}"
            row = [
                gid,
                gp.get("title", ""),
                gp.get("rule", ""),
                gp.get("example", ""),
                gp.get("meaning_ja", ""),
                day,
                f"news:{slug} | source:{record.source}",
            ]
            grammar_lines.append("\t".join(row))

    vocab_path.write_text("\n".join(vocab_lines) + "\n", encoding="utf-8")
    grammar_path.write_text("\n".join(grammar_lines) + "\n", encoding="utf-8")
    return vocab_path, grammar_path


def import_anki(day: str) -> None:
    script = ANKI_ROOT / "scripts" / "import.py"
    for material, batch in [
        ("news-digest-vocabulary", f"{day}-vocabulary.tsv"),
        ("news-digest-grammar", f"{day}-grammar.tsv"),
    ]:
        subprocess.run(
            ["python3", str(script), material, "--batch", batch],
            cwd=ANKI_ROOT,
            check=False,
        )
