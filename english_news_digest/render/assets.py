"""Shared CSS and JS assets."""

from __future__ import annotations

from ..paths import DIST_ASSETS

STYLES_CSS = """
:root {
  --bg: #f8f7f4;
  --surface: #ffffff;
  --surface-soft: #fbfaf7;
  --ink: #1a1917;
  --muted: #6b6560;
  --line: #e8e4dc;
  --accent: #b42318;
  --accent-soft: #fdecea;
  --accent-hover: #8a1c12;
  --world: #1a4d6d;
  --world-soft: #e8f2f8;
  --translation: #2c4a3e;
  --translation-soft: #eef6f1;
  --translation-border: #c5d9ce;
  --grammar-bg: #f3f1ec;
  --deep-bg: #eef3f8;
  --today: #fff8e6;
  --today-ring: #d4a012;
  --focus: #0f6cbf;
  --example-en: #3a3632;
  --comment-raw: #2a2622;
  --comment-standard: #3a3632;
  --cal-comments: #8a5a12;
  --badge-national-bg: #e8f0e8;
  --badge-national-fg: #2d5a2d;
  --badge-crime-bg: #f5e8e8;
  --badge-crime-fg: #8b2e2e;
  --badge-business-bg: #e8edf5;
  --badge-business-fg: #2e4a7a;
  --badge-politics-bg: #f0e8f5;
  --badge-politics-fg: #5a2d6e;
  --badge-tech-bg: #e8f2f5;
  --badge-tech-fg: #2d5a6e;
  --theme-toggle-bg: var(--surface);
  --theme-toggle-border: var(--line);
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
}

[data-theme="dark"] {
  color-scheme: dark;
  --bg: #121110;
  --surface: #1c1b19;
  --surface-soft: #181715;
  --ink: #ece9e4;
  --muted: #a39d95;
  --line: #35302a;
  --accent: #f07167;
  --accent-soft: #3a2220;
  --accent-hover: #ff8a80;
  --world: #7eb8d9;
  --world-soft: #1a2833;
  --translation: #9ec4b0;
  --translation-soft: #1a2a22;
  --translation-border: #3a5248;
  --grammar-bg: #23211f;
  --deep-bg: #1a222c;
  --today: #2a2618;
  --today-ring: #c9a227;
  --focus: #6eb0f0;
  --example-en: #cdc8c2;
  --comment-raw: #e0dbd4;
  --comment-standard: #cdc8c2;
  --cal-comments: #d4a84a;
  --badge-national-bg: #1e2a1e;
  --badge-national-fg: #8fbf8f;
  --badge-crime-bg: #2e1e1e;
  --badge-crime-fg: #e08a8a;
  --badge-business-bg: #1a2433;
  --badge-business-fg: #8aa8d4;
  --badge-politics-bg: #281a30;
  --badge-politics-fg: #c49ad4;
  --badge-tech-bg: #1a2830;
  --badge-tech-fg: #8ab4c4;
  --theme-toggle-bg: var(--surface);
  --theme-toggle-border: var(--line);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  color: var(--ink);
  background: var(--bg);
  font-family: "Source Sans 3", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

a {
  color: var(--accent);
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
}

a:hover { color: var(--accent-hover); }

.page {
  width: min(100% - 32px, 960px);
  margin: 0 auto;
  padding: var(--space-6) 0 56px;
}

.reader-page {
  width: min(100% - 32px, 820px);
}

.panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: var(--space-6);
  margin-bottom: var(--space-4);
}

.breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
  font-size: 14px;
  color: var(--muted);
}

.breadcrumb a {
  color: var(--muted);
  text-decoration: none;
}

.breadcrumb a:hover { color: var(--accent); }

.breadcrumb .sep { color: var(--line); }

.page-header h1,
h1 {
  font-family: "Fraunces", Georgia, serif;
  font-weight: 600;
  font-size: 28px;
  line-height: 1.15;
  margin: 0 0 var(--space-2);
}

.page-header .lede,
.lede {
  color: var(--muted);
  max-width: 52ch;
  margin: var(--space-2) 0 0;
  font-size: 16px;
}

.meta {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.35;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.badge.japan { background: var(--accent-soft); color: var(--accent); }
.badge.world { background: var(--world-soft); color: var(--world); }
.badge.national { background: var(--badge-national-bg); color: var(--badge-national-fg); }
.badge.crime { background: var(--badge-crime-bg); color: var(--badge-crime-fg); }
.badge.business { background: var(--badge-business-bg); color: var(--badge-business-fg); }
.badge.politics { background: var(--badge-politics-bg); color: var(--badge-politics-fg); }
.badge.tech { background: var(--badge-tech-bg); color: var(--badge-tech-fg); }

.summary-ja {
  margin-top: var(--space-4);
  padding: var(--space-4);
  background: var(--grammar-bg);
  border-radius: 8px;
  border-left: 3px solid var(--accent);
  font-size: 16px;
  line-height: 1.65;
}

h2 {
  font-family: "Fraunces", Georgia, serif;
  font-weight: 600;
  font-size: 21px;
  margin: 0 0 var(--space-4);
}

h3 {
  font-family: "Source Sans 3", system-ui, sans-serif;
  font-weight: 600;
  font-size: 18px;
  margin: 0;
  line-height: 1.3;
}

/* Calendar */
.cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.cal-header h2 { margin: 0; font-size: 21px; }

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: var(--space-1);
}

.cal-dow {
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  padding: var(--space-2) 0;
  text-transform: uppercase;
}

.cal-cell {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 15px;
  position: relative;
  color: var(--muted);
  min-height: 44px;
}

.cal-cell.empty { visibility: hidden; }

.cal-cell.has-edition {
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--ink);
  font-weight: 600;
  text-decoration: none;
}

.cal-cell.has-edition:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.cal-cell.today {
  box-shadow: inset 0 0 0 2px var(--today-ring);
  background: var(--today);
}

.cal-count {
  font-size: 11px;
  font-weight: 500;
  color: var(--accent);
  margin-top: 2px;
}

.cal-cell.has-comments {
  position: relative;
}

.cal-comments {
  display: block;
  font-size: 10px;
  font-weight: 600;
  color: var(--cal-comments);
  margin-top: 1px;
  line-height: 1.1;
}

/* Daily list */
.edition-list { margin: 0; padding: 0; list-style: none; }

.article-row {
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: var(--space-4);
  padding: var(--space-5) 0;
  border-bottom: 1px solid var(--line);
}

.article-row:last-child { border-bottom: 0; }

.article-row .rank {
  font-family: "Fraunces", Georgia, serif;
  font-size: 20px;
  font-weight: 600;
  color: var(--muted);
}

.article-row .row-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.article-row .card-title {
  font-family: "Fraunces", Georgia, serif;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.3;
  margin: 0 0 var(--space-2);
}

.article-row .card-title a {
  color: inherit;
  text-decoration: none;
}

.article-row .card-title a:hover { color: var(--accent); }

.article-row .summary {
  font-size: 16px;
  line-height: 1.65;
  margin: 0 0 var(--space-3);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-row .row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  font-size: 14px;
}

.article-row .row-actions .secondary {
  color: var(--muted);
}

/* Article reader */
.sentence-block {
  padding: 22px 0;
  border-bottom: 1px solid var(--line);
}

.sentence-block:last-child { border-bottom: 0; }

.sentence-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.sentence-num {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  margin-bottom: 0;
}

.speak-btn--sentence {
  width: 1.75rem;
  height: 1.75rem;
  min-width: 36px;
  min-height: 36px;
  font-size: 0.75rem;
}

.sentence-en {
  margin: 0;
  font-family: "Fraunces", Georgia, serif;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.55;
}

.translation {
  margin: 10px 0 0;
  padding-left: var(--space-3);
  border-left: 2px solid var(--translation-border);
  color: var(--translation);
  font-size: 16px;
  line-height: 1.65;
}

.grammar-note {
  margin-top: var(--space-3);
  padding: var(--space-3) 14px;
  border-radius: 8px;
  background: var(--grammar-bg);
  font-size: 15px;
  line-height: 1.65;
}

.grammar-note strong {
  color: var(--accent);
  font-weight: 600;
}

.deep-dive {
  margin-top: var(--space-3);
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.deep-dive summary {
  padding: var(--space-3) 14px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: var(--world);
  list-style: none;
}

.deep-dive summary::-webkit-details-marker { display: none; }

.deep-dive[open] {
  background: var(--deep-bg);
  border-left: 3px solid var(--world);
}

.deep-dive .deep-content {
  padding: 0 14px 14px;
}

.chunk-table {
  width: 100%;
  border-collapse: collapse;
  margin: var(--space-2) 0;
  font-size: 14px;
}

.chunk-table th,
.chunk-table td {
  border: 1px solid var(--line);
  padding: var(--space-2) var(--space-3);
  text-align: left;
  vertical-align: top;
}

.chunk-table th {
  background: var(--grammar-bg);
  font-weight: 600;
  font-size: 12px;
  color: var(--muted);
}

.chunk-table .chunk-en {
  font-family: "Fraunces", Georgia, serif;
  font-weight: 500;
}

.chunk-table .chunk-role {
  color: var(--world);
  font-weight: 600;
  white-space: nowrap;
}

.chunk-stack { display: none; }

.chunk-card {
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--line);
}

.chunk-card:last-child { border-bottom: 0; }

.chunk-card .chunk-en {
  font-family: "Fraunces", Georgia, serif;
  font-weight: 500;
  margin-bottom: var(--space-1);
}

.chunk-card .chunk-meta {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: var(--space-1);
}

.deep-text {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--line);
  font-size: 14px;
  line-height: 1.65;
}

.deep-text strong { color: var(--world); }

/* Vocabulary and grammar */
.vocab-grid,
.grammar-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
}

.vocab-card,
.grammar-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: var(--space-4);
  background: var(--surface);
}

.vocab-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.speak-btn {
  border: 1px solid var(--line);
  background: var(--bg);
  border-radius: 50%;
  width: 2rem;
  height: 2rem;
  cursor: pointer;
  font-size: 0.85rem;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 44px;
}

.speak-btn:hover {
  background: var(--accent-soft);
  border-color: var(--accent);
}

.pron {
  color: var(--muted);
  font-size: 14px;
  margin: var(--space-1) 0 var(--space-2);
}

.example-en {
  margin: var(--space-2) 0 var(--space-1);
  font-size: 14px;
  color: var(--example-en);
}

.example-ja {
  margin: 0;
  font-size: 14px;
  color: var(--muted);
}

.reader-controls {
  margin-bottom: var(--space-4);
}

.reader-controls button {
  font-size: 14px;
  padding: 8px 12px;
  border: 1px solid var(--line);
  background: var(--surface);
  border-radius: 8px;
  cursor: pointer;
  min-height: 44px;
}

.source-link {
  margin-top: var(--space-3);
}

.comment-appendix summary {
  cursor: pointer;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  margin-bottom: var(--space-3);
}

.comment-legend {
  font-size: 13px;
  color: var(--muted);
  margin: 0 0 var(--space-4);
}

.comment-card {
  border-top: 1px solid var(--line);
  padding: var(--space-4) 0;
}

.comment-card:first-of-type {
  border-top: 0;
  padding-top: 0;
}

.comment-meta {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: var(--space-2);
}

.comment-raw {
  font-size: 16px;
  line-height: 1.55;
  margin: 0 0 var(--space-2);
  color: var(--comment-raw);
}

.comment-translation {
  font-size: 15px;
  line-height: 1.6;
  margin: 0 0 var(--space-2);
}

.comment-notes,
.comment-marks {
  margin: var(--space-2) 0;
  padding-left: 1.2em;
  font-size: 14px;
  color: var(--muted);
}

.comment-standard {
  font-size: 14px;
  color: var(--comment-standard);
  margin: var(--space-2) 0;
}

.comment-standard .label {
  font-weight: 600;
  color: var(--muted);
}

.mark-symbol {
  font-weight: 700;
  margin-right: 4px;
}

.theme-toggle {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 100;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 44px;
  padding: 8px 12px;
  border: 1px solid var(--theme-toggle-border);
  border-radius: 999px;
  background: var(--theme-toggle-bg);
  color: var(--ink);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

[data-theme="dark"] .theme-toggle {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
}

.theme-toggle:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}

footer {
  color: var(--muted);
  text-align: center;
  font-size: 14px;
  margin-top: var(--space-6);
}

:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 3px;
}

@media (min-width: 641px) {
  .page-header h1, h1 { font-size: 38px; }
  .sentence-en { font-size: 20px; }
  .article-row .card-title { font-size: 20px; }
}

@media (max-width: 640px) {
  .page, .reader-page {
    width: min(100% - 32px, 100%);
    padding-top: 18px;
  }

  .panel { padding: 18px; }

  .article-row {
    grid-template-columns: 1fr;
    gap: var(--space-2);
  }

  .article-row .rank { font-size: 14px; }

  .vocab-grid, .grammar-grid {
    grid-template-columns: 1fr;
  }

  .chunk-table { display: none; }
  .chunk-stack { display: block; }

  .article-row .summary {
    -webkit-line-clamp: 2;
  }
}
"""

THEME_INIT_JS = """
(function () {
  const stored = localStorage.getItem('end-theme');
  const theme = stored === 'light' || stored === 'dark' ? stored : 'dark';
  document.documentElement.setAttribute('data-theme', theme);
})();
"""

READER_JS = """
let cachedEnglishVoice = null;

function isEnglishVoice(voice) {
  return /^en(-|$)/i.test(voice.lang || '');
}

function englishVoiceScore(voice) {
  const name = (voice.name || '').toLowerCase();
  const uri = (voice.voiceURI || '').toLowerCase();
  const blob = name + ' ' + uri;
  let score = 0;

  if (/premium/.test(blob)) score += 100;
  else if (/enhanced/.test(blob)) score += 80;

  const lang = (voice.lang || '').toLowerCase();
  if (lang === 'en-us') score += 30;
  else if (lang.startsWith('en')) score += 15;

  const preferred = [
    'ava', 'allison', 'nathan', 'zoe', 'samantha', 'alex', 'susan', 'karen',
  ];
  for (let i = 0; i < preferred.length; i += 1) {
    if (name.includes(preferred[i])) {
      score += 50 - i * 3;
      break;
    }
  }

  if (voice.localService) score += 5;
  if (/apple|com\\.apple/.test(uri)) score += 10;
  if (/compact|eloquence/.test(blob) && !/premium|enhanced/.test(blob)) score -= 20;

  return score;
}

function pickBestEnglishVoice(voices) {
  const english = voices.filter(isEnglishVoice);
  if (!english.length) return null;
  return english.reduce((best, voice) => (
    englishVoiceScore(voice) > englishVoiceScore(best) ? voice : best
  ));
}

function getBestEnglishVoice() {
  if (!window.speechSynthesis) return null;
  if (cachedEnglishVoice) return cachedEnglishVoice;
  const voices = speechSynthesis.getVoices();
  if (!voices.length) return null;
  cachedEnglishVoice = pickBestEnglishVoice(voices);
  return cachedEnglishVoice;
}

function primeEnglishVoice() {
  if (!window.speechSynthesis) return;
  getBestEnglishVoice();
  speechSynthesis.addEventListener('voiceschanged', () => {
    cachedEnglishVoice = null;
    getBestEnglishVoice();
  });
}

function speakText(btn) {
  const text = btn.dataset.text || btn.dataset.word;
  if (!text || !window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(text);
  const voice = getBestEnglishVoice();
  if (voice) {
    u.voice = voice;
    u.lang = voice.lang;
  } else {
    u.lang = 'en-US';
  }
  u.rate = 0.9;
  speechSynthesis.cancel();
  speechSynthesis.speak(u);
}

function speakWord(btn) {
  speakText(btn);
}

primeEnglishVoice();

function collapseAllDeepDives() {
  document.querySelectorAll('.deep-dive[open]').forEach((el) => {
    el.open = false;
  });
}

function currentTheme() {
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

function updateThemeToggleLabel() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const dark = currentTheme() === 'dark';
  btn.textContent = dark ? '☀️ Light' : '🌙 Dark';
  btn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('end-theme', theme);
  updateThemeToggleLabel();
}

function toggleTheme() {
  setTheme(currentTheme() === 'dark' ? 'light' : 'dark');
}

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', toggleTheme);
    updateThemeToggleLabel();
  }
});
"""


def write_assets() -> None:
    DIST_ASSETS.mkdir(parents=True, exist_ok=True)
    (DIST_ASSETS / "styles.css").write_text(STYLES_CSS.strip() + "\n", encoding="utf-8")
    (DIST_ASSETS / "reader.js").write_text(READER_JS.strip() + "\n", encoding="utf-8")


def page_shell(
    title: str,
    body_html: str,
    *,
    reader_page: bool = False,
    with_speech: bool = False,
    assets_prefix: str = "assets",
) -> str:
    import html as html_lib

    page_class = "reader-page" if reader_page else "page"
    assets = html_lib.escape(assets_prefix)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>{html_lib.escape(title)}</title>
  <script>{THEME_INIT_JS.strip()}</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Source+Sans+3:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{assets}/styles.css">
</head>
<body>
  <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Toggle color theme">🌙 Dark</button>
  <div class="{page_class}">
    {body_html}
  </div>
  <script src="{assets}/reader.js"></script>
</body>
</html>
"""
