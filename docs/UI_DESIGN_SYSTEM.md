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

---

## 4. Implemented Reusable Component Library (Phase 4) [APPROVED & VERIFIED]

The DreamTeal frontend foundation implements an intentional, dark cinematic component library under `frontend/src/components/`:

### 4.1 Layout & Navigation
- **`AppLayout`** (`components/layout/AppLayout.jsx`): Persistent responsive shell wrapping `Navbar`, dynamic page `Outlet`, and `Footer`.
- **`Navbar`** (`components/navigation/Navbar.jsx`): Brand logo with teal mark, desktop navigation links (`Explore`, `Diary`, `Collections`, `Recommendations`), responsive mobile slide-out drawer, active route indicators, and Session Authentication entry.
- **`Footer`** (`components/navigation/Footer.jsx`): Editorial philosophy ("Zero star ratings. 100% qualitative reactions"), universal reactions palette summary, external provider attribution notices, and copyright.

### 4.2 Media Presentation
- **`MediaPosterCard`** (`components/media/MediaPosterCard.jsx`): Aspect-ratio aware (`2:3` for Movies, Series, Manga; `16:9` for Video Games). Gracefully handles missing/broken imagery without layout shifts, overlays category labels and tracking statuses, and renders text-based reaction verdict badge. Zero star ratings.
- **`MediaPosterGrid`** (`components/media/MediaPosterGrid.jsx`): Responsive column grid (2 mobile, 3–4 tablet, 5–6 desktop), skeleton state, and empty state support.
- **`MediaBackdrop`** (`components/media/MediaBackdrop.jsx`): Cinematic backdrop hero presentation with high-contrast gradient scrim layers ensuring text readability.
- **`MediaMetadata`** (`components/media/MediaMetadata.jsx`): Editorial metadata row/panel (category label, release year, genres, theme tags).
- **`MediaCategoryLabel`** (`components/media/MediaCategoryLabel.jsx`): Distinct pill label for Movie, Series, Manga, Manhwa, and Game.
- **`MediaSkeleton`** (`components/media/MediaSkeleton.jsx`): Matching geometry pulse placeholder for poster cards.

### 4.3 Reactions & Tracking
- **`ReactionBadge`** (`components/reactions/ReactionBadge.jsx`): Strictly non-numeric qualitative reaction pill. Always renders text label. Approved tokens: Peak (Electric Gold `#f59e0b`), Loved It (Warm Coral `#fb7185`), Good Time (Radiant Teal `#14b8a6`), Not My Thing (Muted Lavender `#a78bfa`), Skip (Crimson `#e11d48`).
- **`ReactionSelector`** (`components/reactions/ReactionSelector.jsx`): Accessible, keyboard-navigable radio group for selecting qualitative verdicts without stars or emojis. Controlled component.
- **`MediaStatusBadge`** (`components/status/MediaStatusBadge.jsx`): Displays lifecycle states (`In Progress`, `Completed`, `Plan to Experience`, `On Hold`, `Dropped`).
- **`ProgressIndicator`** (`components/status/ProgressIndicator.jsx`): Category-specific indicators (Series: `S2 E5`, Manga: `Ch. 142`, Game: `34.5 hrs • Main Story`) with optional smooth teal progress bar.

### 4.4 Feedback & Feedback Primitives
- **`LoadingSpinner`** (`components/feedback/LoadingSpinner.jsx`): Brand teal accented accessible spinner.
- **`Skeleton`** (`components/feedback/Skeleton.jsx`): Dark surface elevation pulse placeholder.
- **`EmptyState`** (`components/feedback/EmptyState.jsx`): Editorial empty state with icon, headline, description, and optional action button.
- **`ErrorMessage`** (`components/feedback/ErrorMessage.jsx`): Inline and panel error feedback with optional retry callback.

### 4.5 UI Primitives & Authentication
- **`Button`** (`components/ui/Button.jsx`): Primary (teal glow), Secondary (surface-2), Ghost, and Danger variants with loading spinners and focus rings.
- **`Modal`** (`components/ui/Modal.jsx`): Accessible dialog with backdrop blur, focus trap, and Escape key listener.
- **`AuthModal`** (`components/forms/AuthModal.jsx`): Django Session Authentication login dialog with CSRF protection and error reporting.
