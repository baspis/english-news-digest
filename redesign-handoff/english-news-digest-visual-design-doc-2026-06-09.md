# English News Digest Visual Design Doc

作成日: 2026-06-09

## 1. Executive Summary

English News Digest の見た目は、ニュースサイトではなく「毎朝読む英語学習リーダー」として設計します。方向性は、紙面の落ち着き、iPhoneでの読みやすさ、B2学習者が文ごとの解説に自然に入れる情報密度です。現行サンプルの Fraunces + Source Sans 3、オフホワイト背景、Japan/World の色分けは活かします。ただし、深掘り解説は別ページリンクではなく、記事詳細内の主機能として目立ちすぎない展開UIに統合します。

## 2. Design Principles

### 2.1 Quiet learning first

画面は派手にしない。毎日見る前提なので、色・影・装飾は少なく、本文と解説が主役になるようにします。

### 2.2 One decision per screen

- カレンダー: どの日を開くか
- 日次一覧: 5件のうちどれを読むか
- 記事詳細: 今の文を理解するか、深掘りするか

画面内に学習管理、ビルドログ、Anki操作を混ぜません。

### 2.3 Reading rhythm over dashboard density

ダッシュボード風に情報を詰め込まず、読み物としての余白を優先します。特に記事詳細は、1文ごとに呼吸できる間隔を確保します。

### 2.4 Deep dive is calm, not advanced mode

深掘りは「別モード」ではなく「必要な文だけ開く詳しい解説」です。上級者向け・詳細版のように分離せず、同じ画面内で扱います。

## 3. Visual Direction

推奨する方向性:

```text
Calm editorial reader
Japanese learner support
Warm neutral paper
Clear source/category labels
Low-friction mobile reading
```

避ける方向性:

```text
News portal
Analytics dashboard
Gamified learning app
Heavy card grid
Strong gradients
Marketing landing page
```

見た目の印象は、新聞や雑誌の本文ページに近いが、語彙・文法メモが読みやすく整理された学習用リーダーです。

## 4. Design Tokens

### 4.1 Color

現行サンプルの色を出発点にしつつ、少し整理します。

| Token | Value | Use |
| --- | --- | --- |
| `--bg` | `#f8f7f4` | Page background |
| `--surface` | `#ffffff` | Main panels, article surfaces |
| `--surface-soft` | `#fbfaf7` | Subtle nested explanation areas |
| `--ink` | `#1a1917` | Main text |
| `--muted` | `#6b6560` | Metadata, secondary text |
| `--line` | `#e8e4dc` | Borders and dividers |
| `--accent` | `#b42318` | Japan/category accent, primary links |
| `--accent-soft` | `#fdecea` | Japan badge background |
| `--world` | `#1a4d6d` | World/category accent |
| `--world-soft` | `#e8f2f8` | World badge background |
| `--translation` | `#2c4a3e` | Japanese translation text |
| `--translation-soft` | `#eef6f1` | Translation area background if needed |
| `--grammar-bg` | `#f3f1ec` | Grammar notes |
| `--deep-bg` | `#eef3f8` | Deep-dive notes |
| `--today` | `#fff8e6` | Today calendar cell |
| `--today-ring` | `#d4a012` | Today focus ring |
| `--focus` | `#0f6cbf` | Keyboard focus outline |

Color rules:

- Main page should read mostly neutral, not red or blue.
- Use red for Japan and primary actions, blue for World and deep-dive details.
- Do not use full-width colored blocks for learning content.
- Keep warning or build status colors out of the learner-facing UI unless needed.

### 4.2 Typography

Use the current pairing:

```css
--font-display: "Fraunces", Georgia, serif;
--font-body: "Source Sans 3", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
```

Rules:

- Use Fraunces for app title, article titles, and English sentence text.
- Use Source Sans 3 for navigation, metadata, Japanese summaries, grammar notes, vocabulary, and UI labels.
- Do not use viewport-based font scaling.
- Do not use negative letter spacing.
- Keep Japanese text in Source Sans 3/system sans for readability.

Recommended type scale:

| Role | Mobile | Desktop | Weight |
| --- | ---: | ---: | --- |
| App title / page h1 | 28px | 38px | 600 |
| Article title | 26px | 40px | 600 |
| Section h2 | 21px | 24px | 600 |
| Card title | 18px | 20px | 600 |
| English sentence | 18px | 20px | 500 |
| Body Japanese | 16px | 17px | 400 |
| Metadata | 14px | 14px | 500 |
| Badge | 12px | 12px | 700 |

Line-height:

```text
English sentence: 1.55
Japanese body: 1.65
Metadata: 1.35
Card title: 1.3
```

### 4.3 Spacing

Use a simple 4px grid.

| Token | Value | Use |
| --- | ---: | --- |
| `--space-1` | 4px | Tight inline gaps |
| `--space-2` | 8px | Badge/card inner gaps |
| `--space-3` | 12px | Small block gaps |
| `--space-4` | 16px | Standard padding |
| `--space-5` | 20px | Section gap |
| `--space-6` | 24px | Panel padding mobile |
| `--space-8` | 32px | Panel padding desktop |
| `--space-10` | 40px | Major section gap |

### 4.4 Radius, border, shadow

Cards should not look like app-store tiles. Keep edges modest.

```text
Panel radius: 8px
Card radius: 8px
Badge radius: 6px
Calendar cell radius: 8px
Border: 1px solid var(--line)
Shadow: none by default
```

Use shadow only for temporary overlays in Phase 2. Static pages should rely on borders and spacing.

## 5. Page Layout System

### 5.1 Global shell

```text
body
  .page
    .topbar / breadcrumb
    main.content
      header.page-header
      screen-specific content
    footer
```

Recommended widths:

```css
.page {
  width: min(100% - 32px, 960px);
  margin: 0 auto;
  padding: 24px 0 56px;
}

.reader-page {
  width: min(100% - 32px, 820px);
}
```

Use the narrower `reader-page` for article detail. Daily list and calendar can use 960px.

### 5.2 Header style

Header panels should present orientation, not decoration.

Header contains:

- Breadcrumb above or inside topbar
- H1
- One short lede
- Metadata row if useful

Do not put large hero sections, background images, or decorative gradients on this product.

## 6. Screen 1: Calendar

### 6.1 Purpose

The calendar is an entry point, not a content preview. It should show which days are available and let the user choose one quickly.

### 6.2 Layout

Desktop:

```text
+------------------------------------------------------+
| English News Digest                                  |
| Choose a daily edition.                              |
+------------------------------------------------------+
| < May                         June 2026        July > |
+------------------------------------------------------+
| Mon Tue Wed Thu Fri Sat Sun                          |
|  1   2   3   4   5   6   7                           |
|  8  [9] 10  11  12  13  14                           |
|     5                                                   |
+------------------------------------------------------+
```

Mobile:

```text
English News Digest
Choose a daily edition.

< June 2026 >

M T W T F S S
1 2 3 4 5 6 7
8 9 10...
  5
```

### 6.3 Calendar cell states

| State | Visual |
| --- | --- |
| Empty/outside month | Invisible or muted, not clickable |
| No edition | Muted text, no border |
| Complete edition | White surface, border, strong date number, count `5` |
| Today | Pale yellow background plus inner ring |
| Today + complete | Combine complete border with today ring |
| Hover | Soft accent background |
| Focus | Blue outline, 2px offset |

Cell content:

```text
9
5
```

Do not show article titles on the calendar.

## 7. Screen 2: Daily Article List

### 7.1 Purpose

The day page answers: "Which of today's five should I read?"

### 7.2 Layout recommendation

Use one vertical list of five articles, not a two-column Japan/World split.

Reason: the product promise is five learning slots. A two-column split makes the day feel like a source dashboard and creates awkward empty World panels. Category should be a label inside each article row.

Desktop:

```text
Calendar < 2026-06-09

2026年6月9日（火）
5 articles · Japan 3 / World 2 · Generated 07:15 JST

+------------------------------------------------------+
| 01  [JAPAN] Japan Today Crime       14 sentences     |
|     Memorial service marks 25 years...               |
|     大阪府池田市の小学校で...                         |
|     Source date Jun 8        Open article   Original |
+------------------------------------------------------+
| 02  [WORLD] BBC Asia                18 sentences     |
|     ...                                              |
+------------------------------------------------------+
```

Mobile:

```text
2026年6月9日（火）
5 articles

01  JAPAN
Memorial service marks 25 years...
大阪府池田市の小学校で...
14 sentences · 8 vocabulary
Open article
```

### 7.3 Article row anatomy

Each article row has:

1. Rank number `01` to `05`.
2. Category badge: `JAPAN` or `WORLD`.
3. Source name and source section.
4. Sentence count and vocabulary count.
5. Title.
6. Japanese summary, max 2 lines on mobile and 3 lines on desktop.
7. Source date only if different from edition date.
8. Primary link: article detail.
9. Secondary link: original source.

Avoid a separate "deep version" link.

### 7.4 Empty category handling

Do not show an empty World panel. If all five are Japan, show:

```text
5 articles · Japan 5 / World 0
```

This is enough. The UI should not make the absence of World articles feel like failure.

## 8. Screen 3: Article Detail

### 8.1 Purpose

The article detail screen is the main learning surface. It should help the user read the article sentence by sentence without losing the original English flow.

### 8.2 Page structure

```text
Breadcrumb

Article header
  Category badge
  Article title
  Source metadata
  Japanese summary

Reading controls
  [Translations on] [Grammar notes on] [Collapse all deep dives]

Sentence list
  Sentence card 1
  Sentence card 2
  ...

Vocabulary

Grammar focus
```

Reading controls are useful but should be minimal. MVP can include only "Collapse all deep dives" if toggles are too much.

### 8.3 Sentence block anatomy

```text
+------------------------------------------------------+
| 01                                                   |
| A memorial service was held Sunday to mark...        |
|                                                      |
| 大阪府池田市の小学校で...                            |
|                                                      |
| 文法: was held は受動態で...                         |
|                                                      |
| [文節ごとに見る v]                                   |
+------------------------------------------------------+
```

Expanded:

```text
+------------------------------------------------------+
| [文節ごとに見る ^]                                   |
| A memorial service        主語        追悼式が        |
| was held Sunday           述語        日曜日に行われた |
| to mark...                目的        25周年を...     |
|                                                      |
| 深掘り: leave + O + adj. はニュースで...             |
+------------------------------------------------------+
```

### 8.4 Sentence visual rules

- English sentence is the largest text in the block.
- Japanese translation is green-toned text with a subtle left border.
- Grammar note sits in a warm neutral box.
- Deep-dive area uses cool blue background so it is visually distinct from grammar.
- Sentence number is small and muted, but visible for orientation.
- Long tables must not overflow on mobile; chunk rows should stack on small screens.

Mobile chunk layout:

```text
A memorial service
主語 · 追悼式が
memorial service は...
```

Desktop chunk layout may use a table.

## 9. Components

### 9.1 Breadcrumb

Use text links with separators.

```text
Calendar < 2026-06-09 < Article title
```

Style:

```text
font-size: 14px
color: muted
gap: 8px
margin-bottom: 16px
```

Breadcrumb should wrap on mobile.

### 9.2 Badge

```text
JAPAN  red text on red-soft background
WORLD  blue text on blue-soft background
```

Keep badges compact. Do not use full pill bars.

### 9.3 Primary article link

Daily list article row should be clickable through title and an explicit text link:

```text
Open article
```

Use text links, not large filled buttons. This is a reader, not a transactional app.

### 9.4 Original source link

Use a secondary text link:

```text
Original ↗
```

It should never be visually stronger than the learning page link.

### 9.5 Expand deep dive

Use native `<details><summary>` if possible.

Label:

```text
文節ごとに見る
```

Do not label it "詳細版" or "deep mode".

Closed state:

```text
border: 1px solid var(--line)
background: var(--surface-soft)
```

Open state:

```text
background: var(--deep-bg)
border-left: 3px solid var(--world)
```

### 9.6 Vocabulary card

Vocabulary cards can stay as repeated cards because they are independent items.

Desktop:

```text
2-column grid
```

Mobile:

```text
1-column list
```

Each card:

```text
word / phrase
pronunciation
meaning_ja
example
example_ja
small play icon if speech is kept
```

Use an icon button for speech playback. Do not use text button labels for this.

### 9.7 Grammar card

Grammar cards should be quieter than sentence blocks.

Use:

```text
title
one rule paragraph
example sentence
Japanese explanation
```

Avoid long walls of grammar at the bottom. If grammar content grows, Phase 2 should group it by pattern.

## 10. Responsive Behavior

### Mobile first

Primary target is iPhone reading. Start from 360-430px viewport.

Rules:

- Page horizontal padding: 16px.
- Article detail width: full available width.
- Daily list: one column.
- Vocabulary and grammar: one column.
- Calendar cells: fixed square or near-square with stable dimensions.
- Chunk explanations stack vertically.
- No text should be hidden behind horizontal scroll.

### Tablet/Desktop

Rules:

- Page width max 960px.
- Article detail max 820px.
- Daily list remains one column.
- Vocabulary/grammar can use two columns.
- Do not create a sidebar in MVP.

Reason: a sidebar would add scanning burden and is not needed for the 3-screen learning flow.

## 11. Accessibility and Readability

Minimum requirements:

- Body text contrast should meet WCAG AA.
- All interactive elements must have visible focus state.
- Calendar active dates must be links or buttons with accessible names.
- Color must not be the only category indicator; badges need text labels.
- `<details>` summaries must be keyboard accessible.
- Original links opening new tabs should use `rel="noopener"`.
- Tap targets should be at least 44px tall where practical.
- Article row title links should not be tiny.

Japanese/English mixed reading:

- Do not italicize Japanese text.
- Keep English examples in the display serif only when they are primary reading content.
- In vocabulary cards, examples can be body font or italic body font, but avoid making the entire card look like prose.

## 12. CSS Structure Recommendation

Move inline CSS into a shared stylesheet:

```text
dist/assets/styles.css
```

Suggested sections:

```css
/* 1. Tokens */
/* 2. Base */
/* 3. Layout */
/* 4. Typography */
/* 5. Navigation */
/* 6. Calendar */
/* 7. Daily list */
/* 8. Article reader */
/* 9. Vocabulary and grammar */
/* 10. Utilities */
```

Class naming can stay simple:

```text
.page
.reader-page
.breadcrumb
.page-header
.edition-list
.article-row
.sentence-block
.translation
.grammar-note
.deep-dive
.vocab-grid
.vocab-card
.grammar-grid
.grammar-card
```

Avoid one-off inline styles in generated HTML.

## 13. Example CSS Skeleton

```css
:root {
  --bg: #f8f7f4;
  --surface: #ffffff;
  --surface-soft: #fbfaf7;
  --ink: #1a1917;
  --muted: #6b6560;
  --line: #e8e4dc;
  --accent: #b42318;
  --accent-soft: #fdecea;
  --world: #1a4d6d;
  --world-soft: #e8f2f8;
  --translation: #2c4a3e;
  --translation-soft: #eef6f1;
  --grammar-bg: #f3f1ec;
  --deep-bg: #eef3f8;
  --today: #fff8e6;
  --today-ring: #d4a012;
  --focus: #0f6cbf;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  color: var(--ink);
  background: var(--bg);
  font-family: "Source Sans 3", system-ui, sans-serif;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

.page {
  width: min(100% - 32px, 960px);
  margin: 0 auto;
  padding: 24px 0 56px;
}

.reader-page {
  width: min(100% - 32px, 820px);
}

.panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 24px;
}

.article-row {
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 16px;
  padding: 20px 0;
  border-bottom: 1px solid var(--line);
}

.sentence-block {
  padding: 22px 0;
  border-bottom: 1px solid var(--line);
}

.sentence-en {
  margin: 0;
  font-family: "Fraunces", Georgia, serif;
  font-size: 20px;
  line-height: 1.55;
}

.translation {
  margin: 10px 0 0;
  padding-left: 12px;
  border-left: 2px solid #c5d9ce;
  color: var(--translation);
}

.grammar-note {
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: 8px;
  background: var(--grammar-bg);
}

.deep-dive[open] {
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: 8px;
  border-left: 3px solid var(--world);
  background: var(--deep-bg);
}

:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 3px;
}

@media (max-width: 640px) {
  .page,
  .reader-page {
    width: min(100% - 32px, 100%);
    padding-top: 18px;
  }

  .panel {
    padding: 18px;
  }

  .article-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .sentence-en {
    font-size: 18px;
  }
}
```

## 14. Implementation Acceptance Checklist

Visual implementation is acceptable when:

1. Calendar has no article previews and active dates are clearly clickable.
2. Daily page shows exactly five rows in one clear sequence.
3. Japan/World are labels, not layout columns.
4. No "詳細版" or `.deep.html` link appears in learner-facing UI.
5. Article detail reads comfortably on iPhone width.
6. Each sentence has English, translation, grammar, and optional chunk expansion in that order.
7. Chunk explanations do not overflow horizontally on mobile.
8. Vocabulary and grammar sections are visually secondary to sentence reading.
9. Focus states are visible.
10. The page does not depend on decorative images, gradients, or large shadows.

## 15. Final Visual Decisions

| Topic | Decision |
| --- | --- |
| Visual style | Calm editorial reader |
| Main layout | Single-column reader flow |
| Fonts | Fraunces for titles/English, Source Sans 3/system sans for UI/Japanese |
| Color | Warm neutral base, red for Japan/action, blue for World/deep dive |
| Calendar | Date selection only, active days show count |
| Daily list | One vertical list of five articles |
| Article detail | Sentence-first reader with expandable chunks |
| Deep dive | `<details>` per sentence; no separate detail page |
| Cards | Use only for repeated vocabulary/grammar items, not nested page sections |
| Mobile | Primary design target |
