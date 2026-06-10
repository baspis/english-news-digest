"""Article detail renderer."""

from __future__ import annotations

import html

from ..comments import load_comments, render_community_appendix
from ..schemas import ArticleRecord, Edition
from .assets import page_shell


def render_chunks_table(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    rows = []
    stack = []
    for ch in chunks:
        rows.append(
            f"<tr>"
            f"<td class='chunk-en'>{html.escape(ch.get('text', ''))}</td>"
            f"<td class='chunk-role'>{html.escape(ch.get('role_ja', ''))}</td>"
            f"<td>{html.escape(ch.get('literal_ja', ''))}</td>"
            f"<td>{html.escape(ch.get('note_ja', ''))}</td>"
            f"</tr>"
        )
        stack.append(
            f"""
            <div class="chunk-card">
              <div class="chunk-en">{html.escape(ch.get('text', ''))}</div>
              <div class="chunk-meta">{html.escape(ch.get('role_ja', ''))} · {html.escape(ch.get('literal_ja', ''))}</div>
              <div>{html.escape(ch.get('note_ja', ''))}</div>
            </div>
            """
        )
    return f"""
    <table class="chunk-table">
      <thead><tr>
        <th>文節</th><th>役割</th><th>直訳</th><th>解説</th>
      </tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    <div class="chunk-stack">{''.join(stack)}</div>
    """


def render_sentence_block(idx: int, sent: dict) -> str:
    chunks = sent.get("chunks", [])
    deep_dive = sent.get("deep_dive_ja", "")
    has_deep = bool(chunks or deep_dive)

    deep_html = ""
    if has_deep:
        inner = render_chunks_table(chunks)
        if deep_dive:
            inner += f'<div class="deep-text"><strong>深掘り:</strong> {html.escape(deep_dive)}</div>'
        deep_html = f"""
        <details class="deep-dive">
          <summary>文節ごとに見る</summary>
          <div class="deep-content">{inner}</div>
        </details>
        """

    sid = sent.get("sentence_id", f"s{idx:03d}")
    text = sent.get("text", "")
    return f"""
    <article class="sentence-block" id="{html.escape(sid)}">
      <div class="sentence-head">
        <div class="sentence-num">{idx:02d}</div>
        <button type="button" class="speak-btn speak-btn--sentence" data-text="{html.escape(text, quote=True)}"
                onclick="speakText(this)" aria-label="英文を読み上げ">&#9654;</button>
      </div>
      <p class="sentence-en">{html.escape(text)}</p>
      <p class="translation">{html.escape(sent.get('translation_ja', ''))}</p>
      <div class="grammar-note"><strong>文法:</strong> {html.escape(sent.get('grammar_ja', ''))}</div>
      {deep_html}
    </article>
    """


def render_article_page(
    edition: Edition,
    record: ArticleRecord,
    analysis: dict,
) -> str:
    sentences_html = []
    for idx, sent in enumerate(analysis.get("sentences", []), start=1):
        sentences_html.append(render_sentence_block(idx, sent))

    vocab_html = []
    for vocab in analysis.get("vocabulary", []):
        word = vocab.get("word", "")
        vocab_html.append(
            f"""
            <div class="vocab-card">
              <div class="vocab-head">
                <h3>{html.escape(word)}</h3>
                <button type="button" class="speak-btn" data-text="{html.escape(word, quote=True)}"
                        onclick="speakText(this)" aria-label="発音を再生">&#9654;</button>
              </div>
              <div class="pron">{html.escape(vocab.get('pronunciation', ''))}</div>
              <p>{html.escape(vocab.get('meaning_ja', ''))}</p>
              <p class="example-en"><em>{html.escape(vocab.get('example', ''))}</em></p>
              <p class="example-ja">{html.escape(vocab.get('example_ja', ''))}</p>
            </div>
            """
        )

    grammar_html = []
    for gp in analysis.get("grammar_points", []):
        grammar_html.append(
            f"""
            <div class="grammar-card">
              <h3>{html.escape(gp.get('title', ''))}</h3>
              <p>{html.escape(gp.get('rule', ''))}</p>
              <p class="example-en"><em>{html.escape(gp.get('example', ''))}</em></p>
              <p>{html.escape(gp.get('meaning_ja', ''))}</p>
            </div>
            """
        )

    edition_url = f"../index.html"
    short_title = record.title if len(record.title) < 48 else record.title[:45] + "..."

    body = f"""
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <a href="../../../index.html">Calendar</a>
      <span class="sep">/</span>
      <a href="{edition_url}">{html.escape(edition.edition_date)}</a>
      <span class="sep">/</span>
      <span>{html.escape(short_title)}</span>
    </nav>
    <header class="panel page-header">
      <span class="badge {html.escape(record.category)}">{html.escape(record.category)}</span>
      <h1>{html.escape(record.title)}</h1>
      <div class="meta">{html.escape(record.source)} · {html.escape(record.source_published_date_jst)}</div>
      <div class="summary-ja">{html.escape(analysis.get('summary_ja', ''))}</div>
      <p class="meta source-link">
        <a href="{html.escape(record.source_url, quote=True)}" target="_blank" rel="noopener">Original ↗</a>
      </p>
    </header>

    <section class="panel">
      <div class="reader-controls">
        <button type="button" onclick="collapseAllDeepDives()">
          Collapse all deep dives
        </button>
      </div>
      {''.join(sentences_html)}
    </section>

    <section class="panel">
      <h2>Vocabulary</h2>
      <div class="vocab-grid">{''.join(vocab_html)}</div>
    </section>

    <section class="panel">
      <h2>Grammar focus</h2>
      <div class="grammar-grid">{''.join(grammar_html)}</div>
    </section>

    {render_community_appendix(load_comments(record.article_id))}

    <footer>English News Digest · {html.escape(edition.edition_date)}</footer>
    """
    return page_shell(
        record.title,
        body,
        reader_page=True,
        with_speech=True,
        assets_prefix="../../../assets",
    )
