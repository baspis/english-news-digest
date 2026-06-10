"""Article detail renderer."""

from __future__ import annotations

import html

from ..comments import load_comments, render_community_appendix
from ..schemas import ArticleRecord, Edition
from .assets import page_shell
from .speech import speak_button


def render_chunks_table(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    rows = []
    stack = []
    for ch in chunks:
        chunk_text = ch.get("text", "")
        chunk_btn = speak_button(chunk_text, compact=True)
        rows.append(
            f"<tr>"
            f"<td class='chunk-en'><span class='speak-line'>{html.escape(chunk_text)}"
            f"{chunk_btn}</span></td>"
            f"<td class='chunk-role'>{html.escape(ch.get('role_ja', ''))}</td>"
            f"<td>{html.escape(ch.get('literal_ja', ''))}</td>"
            f"<td>{html.escape(ch.get('note_ja', ''))}</td>"
            f"</tr>"
        )
        stack.append(
            f"""
            <div class="chunk-card">
              <div class="chunk-en speak-line">{html.escape(chunk_text)}{chunk_btn}</div>
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
        {speak_button(text, aria_label="英文を読み上げ")}
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
        example = vocab.get("example", "")
        vocab_html.append(
            f"""
            <div class="vocab-card">
              <div class="vocab-head">
                <h3>{html.escape(word)}</h3>
                {speak_button(word, aria_label="発音を再生")}
              </div>
              <div class="pron">{html.escape(vocab.get('pronunciation', ''))}</div>
              <p>{html.escape(vocab.get('meaning_ja', ''))}</p>
              <p class="example-en speak-line"><em>{html.escape(example)}</em>{speak_button(example, compact=True)}</p>
              <p class="example-ja">{html.escape(vocab.get('example_ja', ''))}</p>
            </div>
            """
        )

    grammar_html = []
    for gp in analysis.get("grammar_points", []):
        title = gp.get("title", "")
        rule = gp.get("rule", "")
        example = gp.get("example", "")
        grammar_html.append(
            f"""
            <div class="grammar-card">
              <div class="grammar-head">
                <h3>{html.escape(title)}</h3>
                {speak_button(title, compact=True)}
              </div>
              <p class="speak-line">{html.escape(rule)}{speak_button(rule, compact=True)}</p>
              <p class="example-en speak-line"><em>{html.escape(example)}</em>{speak_button(example, compact=True)}</p>
              <p>{html.escape(gp.get('meaning_ja', ''))}</p>
            </div>
            """
        )

    edition_url = f"../index.html"
    short_title = record.title if len(record.title) < 48 else record.title[:45] + "..."

    body = f"""
    <nav class="breadcrumb speak-line" aria-label="Breadcrumb">
      <a href="../../../index.html">Calendar</a>
      {speak_button("Calendar", compact=True)}
      <span class="sep">/</span>
      <a href="{edition_url}">{html.escape(edition.edition_date)}</a>
      <span class="sep">/</span>
      <span>{html.escape(short_title)}</span>
      {speak_button(short_title, compact=True)}
    </nav>
    <header class="panel page-header">
      <div class="title-head">
        <span class="badge {html.escape(record.category)}">{html.escape(record.category)}</span>
        {speak_button(record.category, aria_label="カテゴリを読み上げ", compact=True)}
      </div>
      <div class="title-head">
        <h1>{html.escape(record.title)}</h1>
        {speak_button(record.title, aria_label="タイトルを読み上げ")}
      </div>
      <p class="meta speak-line">{html.escape(record.source)}{speak_button(record.source, compact=True)}
        · {html.escape(record.source_published_date_jst)}</p>
      <div class="summary-ja">{html.escape(analysis.get('summary_ja', ''))}</div>
      <p class="meta source-link speak-line">
        <a href="{html.escape(record.source_url, quote=True)}" target="_blank" rel="noopener">Original ↗</a>
        {speak_button("Original", compact=True)}
      </p>
    </header>

    <section class="panel">
      <div class="reader-controls speak-line">
        <button type="button" onclick="collapseAllDeepDives()">
          Collapse all deep dives
        </button>
        {speak_button("Collapse all deep dives", compact=True)}
      </div>
      {''.join(sentences_html)}
    </section>

    <section class="panel">
      <h2 class="speak-line">Vocabulary{speak_button("Vocabulary", compact=True)}</h2>
      <div class="vocab-grid">{''.join(vocab_html)}</div>
    </section>

    <section class="panel">
      <h2 class="speak-line">Grammar focus{speak_button("Grammar focus", compact=True)}</h2>
      <div class="grammar-grid">{''.join(grammar_html)}</div>
    </section>

    {render_community_appendix(load_comments(record.article_id))}

    <footer class="speak-line">English News Digest · {html.escape(edition.edition_date)}
      {speak_button("English News Digest", compact=True)}</footer>
    """
    return page_shell(
        record.title,
        body,
        reader_page=True,
        with_speech=True,
        assets_prefix="../../../assets",
    )
