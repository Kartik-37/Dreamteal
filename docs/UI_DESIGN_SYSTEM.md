# DreamTeal UI/UX Design System Specification

## 1. Design Philosophy
DreamTeal's design is **dark, poster-focused, functional, and compact**. It takes visual inspiration from cinema platforms like Moctale and media logs like Letterboxd while maintaining its distinct brand identity.

---

## 2. Color Palette & Typography

### Colors
- **Background Deep**: `#0b0c10` (Pitch slate dark)
- **Surface Elevation 1**: `#121318` (Card & panel surface)
- **Surface Elevation 2**: `#1a1c23` (Interactive hover & dropdown surface)
- **Border Neutral**: `#272932` (Subtle divider border)
- **Text Primary**: `#f1f3f9` (High contrast crisp off-white)
- **Text Secondary**: `#9498a8` (Muted gray label text)
- **Accent Primary**: `#14b8a6` (DreamTeal teal glow `#0d9488` / `#14b8a6`)

---

## 3. UI Component Standards

### 3.1 Media Cards
- **Aspect Ratios**:
  - Movies, TV Series, Manga: `2:3` vertical poster ratio.
  - Video Games: `16:9` landscape or `3:4` cover ratio.
- **Card Hover Elements**:
  - Soft overlay transition displaying quick action buttons (`Mark Watched`, `Log Entry`, `Add to Collection`).
  - Subtle 2px elevate transform (no gaudy bouncy animations).

### 3.2 Navigation Bar
- Top persistent header bar:
  - Brand Logo ("DreamTeal" with subtle teal mark).
  - Navigation links: `Explore / Catalog`, `Diary / History`, `My Collections`, `Recommendations`.
  - Global Search Bar (instant modal or dropdown search).
  - Quick `+ Log` button.
  - User Avatar dropdown menu.

### 3.3 DreamTeal Universal Qualitative Reaction Badge System [APPROVED]
- **Design Philosophy**: First-class DreamTeal brand identity. Sleek, compact, qualitative pop-culture reaction badges. Distinctive and modern without copying Moctale or Letterboxd.
- **Strictly Non-Numeric**: Zero stars, zero numeric equivalents, not presented as a "5-star substitute".
- **Visual Identity (Color & Typography)**:
  - **No Emoji or Icons**: Badges do NOT use emojis or generic icon sets. Visual distinction is created strictly through typography, badge geometry, text labels, and dedicated color tokens.
  - **Always Show Text Label**: Text labels are always rendered; color is never used as the sole indicator of meaning (ensuring visual clarity and accessibility).
- **Approved Reaction Design Tokens**:
  - `--reaction-peak-color`: `#f59e0b` (Electric Gold text/accent)
  - `--reaction-peak-bg`: `rgba(245, 158, 11, 0.12)`
  - `--reaction-peak-border`: `rgba(245, 158, 11, 0.35)`
  - `--reaction-loved-it-color`: `#fb7185` (Warm Coral text/accent)
  - `--reaction-loved-it-bg`: `rgba(251, 113, 133, 0.12)`
  - `--reaction-loved-it-border`: `rgba(251, 113, 133, 0.35)`
  - `--reaction-good-time-color`: `#14b8a6` (Radiant Teal text/accent)
  - `--reaction-good-time-bg`: `rgba(20, 184, 166, 0.12)`
  - `--reaction-good-time-border`: `rgba(20, 184, 166, 0.35)`
  - `--reaction-not-my-thing-color`: `#a78bfa` (Muted Lavender text/accent)
  - `--reaction-not-my-thing-bg`: `rgba(167, 139, 250, 0.12)`
  - `--reaction-not-my-thing-border`: `rgba(167, 139, 250, 0.35)`
  - `--reaction-skip-color`: `#e11d48` (Crimson text/accent)
  - `--reaction-skip-bg`: `rgba(225, 29, 72, 0.12)`
  - `--reaction-skip-border`: `rgba(225, 29, 72, 0.35)`

- **The 5 Approved Reactions**:
  1. **Peak**: Electric Gold — An exceptional experience that the user strongly recommends.
  2. **Loved It**: Warm Coral — A genuinely enjoyable experience that the user highly values.
  3. **Good Time**: Radiant Teal — Enjoyable and worth experiencing, but not exceptional.
  4. **Not My Thing**: Muted Lavender — The user did not connect with it, even if the media may have strengths.
  5. **Skip**: Crimson — The user would not recommend spending time on it.

- **Contextual Applications**:
  - *Media Cards*: Compact pill badge with uppercase typography label.
  - *Media Detail Pages*: Prominent verdict pill with bold label and editorial explanation.
  - *Review Cards*: Clean header chip displaying the reviewer's verdict.
  - *Diary History Timeline*: Compact inline text badge.
  - *User Profile Activity*: Qualitative breakdown summary (e.g. "Loved It: 42 • Peak: 18 • Good Time: 35").

### 3.4 Letterboxd-Style Diary UI [APPROVED]
- **Timeline Layout**: Chronological presentation grouped by year and month.
- **Line Items**: Displays poster thumbnail, title, release year, rewatch icon (`🔁`), progress snapshot badge (e.g. `S2E5`, `Ch. 142`), session notes snippet, and quick edit action.
- **Controlled Edit Modal**: Allows updating log date, session notes, progress snapshot, or rewatch toggle in place.

### 3.5 Anti-Patterns to Avoid (Strictly Enforced)
- ❌ NO Star rating displays (no yellow stars, star filters, or star badges).
- ❌ NO Overused glassmorphism / full-page backdrop blurs.
- ❌ NO Bright purple neon glow borders or arbitrary gradients.
- ❌ NO Empty dashboard panels or fluff statistics.
