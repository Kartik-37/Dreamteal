# DreamTeal Product Requirements Document (PRD)

## 1. Executive Summary
DreamTeal is a unified pop-culture tracking, logging, reviewing, collection, discovery, and recommendation web application for **Movies**, **TV Series**, **Manga/Manhwa (Webtoons)**, and **Video Games**.

---

## 2. Core Functional Requirements

### 2.1 Multi-Media Catalog Management
The platform must support four core media categories with specialized metadata and tracking capabilities:

1. **Movies**:
   - Metadata: Title, poster, backdrop, release year, runtime, director, studio, genres, summary, streaming/OTT availability.
   - User Statuses: `Plan to Watch`, `Watching`, `Watched`, `Dropped`.

2. **TV Series**:
   - Metadata: Title, poster, backdrop, release years, total seasons, total episodes, creators, network/platform, genres, summary.
   - User Statuses: `Plan to Watch`, `Watching`, `Completed`, `Paused`, `Dropped`.
   - Granular Progress: Season number, episode number, last watched date.

3. **Manga & Manhwa / Webtoons**:
   - Metadata: Title, poster, banner, release status (Ongoing/Completed), total chapters, author, artist, media sub-type (`Manga`, `Manhwa`, `Manhua`, `Webtoon`), genres, synopsis.
   - User Statuses: `Plan to Read`, `Reading`, `Completed`, `Paused`, `Dropped`.
   - Granular Progress: Current chapter reached, total chapters available.

4. **Video Games**:
   - Metadata: Title, cover image, banner/screenshot, developer, publisher, release year, supported platforms (`PC`, `PlayStation`, `Xbox`, `Switch`, `Mobile`), genres, summary.
   - User Statuses: `Backlog / Plan to Play`, `Playing`, `Finished`, `Paused`, `Abandoned / Dropped`.
   - Granular Progress: Total hours played, completion status (`Main Story`, `Main + Extra`, `100% Completionist`).

---

### 2.2 Strict Requirement: NO Star Ratings [APPROVED]
- Star ratings (e.g., 0.5 to 5.0 stars) are **completely excluded** from the application.
- All database schemas, API representations, UI components, filters, and recommendation calculations must operate without numeric star ratings.

---

### 2.3 Universal Reaction-Based Review System [APPROVED]
- Reviews are separate entities from activity logs.
- DreamTeal uses ONE universal qualitative reaction system across all 5 media categories: **Movies**, **TV Series**, **Manga**, **Manhwa / Webtoons**, and **Video Games**.
- **Zero Star Ratings**: No 1–5 stars, no 0.5 decimal increments, no scores out of 10, no average rating scores.
- **Approved Reaction Taxonomy & Definitions**:
  1. **Peak**: An exceptional experience that the user strongly recommends. (*Color: Electric Gold*)
  2. **Loved It**: A genuinely enjoyable experience that the user highly values. (*Color: Warm Coral*)
  3. **Good Time**: Enjoyable and worth experiencing, but not exceptional. (*Color: Radiant Teal*)
  4. **Not My Thing**: The user did not connect with it, even if the media may have strengths. (*Color: Muted Lavender*)
  5. **Skip**: The user would not recommend spending time on it. (*Color: Crimson*)
- **Critical Architectural Rules**:
  - These are strictly qualitative reactions, NOT hidden numeric ratings.
  - Do NOT internally map them to stars (e.g. Peak != 5 stars).
  - Do NOT display numerical equivalents anywhere in UI or API.
  - Do NOT describe the system as a "5-star alternative".
  - **No Emoji or Icons**: Reaction badges rely on dedicated typography, text labels, and color design tokens. No emojis or generic icon sets are stored or required. Text labels are always shown; color is never the sole indicator of meaning.
  - Implemented via dynamic `ReactionDefinition` models (seeded with these 5 definitions; decoupled from review records).
- **Review Components**:
  - Selected Reaction Badge (linked dynamically via Foreign Key to `ReactionDefinition`).
  - Written review text (optional or rich markdown).
  - Spoiler toggle (`contains_spoilers`).
  - Visibility setting (`public` vs `private`).
  - Creation & edit timestamps.
  - Uniqueness: One active review per user per media item (`UniqueTogether(user, media_item)`).

---

### 2.4 Activity & Diary Logging System [APPROVED]
- **Core Concept**: "History-preserving diary records that users can edit through controlled log editing."
- A diary entry represents: *"I consumed this on this date."*
- A review represents: *"This is how I feel about this media."*
- **Consumption History Preservation**:
  - Each diary entry records a specific consumption event at a point in time.
  - Individual diary records remain strictly separate rows with unique identifiers.
  - Multiple rewatches, re-reads, or replays are represented as separate, discrete diary log records (never collapsed into a single row or overwriting past logs).
- **Controlled Log Editing**:
  - Users can edit an existing diary entry through controlled log editing.
  - **Editable fields**: `logged_date`, `is_rewatch_or_replay`, `session_notes`, `progress_snapshot`.
  - **Non-editable fields / Safeguards**: Editing a record only mutates that specific record; it cannot clobber or merge other historical entries.
- **Automatic Diary → Progress Synchronization [APPROVED]**:
  - **Default Behavior**: When a user creates a diary log, the active progress is updated automatically.
  - **Forward Progress Rule**:
    - TV Series: Current is Season 2 Episode 3 + Diary logs Episode 4 $\rightarrow$ Current becomes Episode 4.
    - Manga/Manhwa: Current is Chapter 80 + Diary logs Chapter 84 $\rightarrow$ Current becomes Chapter 84.
    - Video Games: Current hours = 12 + Diary logs session of 2.5 hours $\rightarrow$ Current hours becomes 14.5 hours.
  - **Historical Non-Reversal Rule**:
    - Historical diary entries must NEVER accidentally move current progress backwards.
    - Example: Current is Season 2 Episode 8; user logs a past session for Season 2 Episode 4 $\rightarrow$ Diary entry is saved as Episode 4, but Current progress remains Episode 8.
    - Example: Current is Chapter 84; user logs past session for Chapter 70 $\rightarrow$ Diary entry is saved as Chapter 70, Current remains 84.
  - **Game Completion Rules**:
    - Logging a game session accumulates `hours_played`.
    - If the diary entry specifies completion (`completion_type`: `Main Story`, `Main + Extra`, `100% Completionist`), active progress updates completion type and can advance `UserMediaStatus` to `Finished`.
  - **Opt-Out Control**: Logging UI and API provide an optional flag (`sync_progress: false`) to bypass automatic progress updates for specific edge cases, but automatic sync remains the default.
- **Diary Entry Deletion**:
  - Deleting a diary entry removes only that individual consumption event from the user's historical log timeline.
  - Deleting an entry does NOT delete the media item from the catalog, does not erase unrelated log entries, and does not automatically reset overall `UserMediaStatus` unless explicitly requested or if no further log activity remains.

---

### 2.5 In-House Recommendation & Discovery Engine
- Dedicated to answering: *"What should I watch/read/play next?"* directly within DreamTeal.
- **Recommendation Architecture**: APPROVED (Deterministic & rule-based first).
- **Exact Scoring Formula & Metric Weights**: PROVISIONAL / NOT FINALIZED (Numeric weights and balance between genres, tags, and reaction affinities are subject to tuning).
- Planned scoring dimensions:
  - Genre and tag similarity.
  - Vibe and thematic cross-matching (e.g. matching dark sci-fi anime to cyberpunk video games or dystopian manhwa).
  - User consumption history and reaction affinity.
  - Direct "Similar Media" curated cross-references.

---

### 2.6 Personal Collections & Lists [PROPOSED]
- Users can create themed public or private collections (e.g. *"Must-Play Tactical RPGs"*, *"Mind-Bending Movies under 2 Hours"*, *"Peak Action Manhwa"*).
- Ability to bookmark and like community collections.

---

### 2.7 User Authentication & Multi-User Architecture [APPROVED]
- **Mechanism**: Standard Django Session Authentication + CSRF protection (`django.contrib.auth.models.User`).
- **No JWT**: Token-based authentication / JWT is excluded unless a future requirement specifically requires it.
- **Frontend Communication**: React frontend communicates safely with Django REST API using browser session cookies (`sessionid`) and CSRF tokens (`csrftoken`).
- **Deployment & Development Considerations**:
  - *Local Development*: Vite dev server proxies `/api/` requests to Django at `http://127.0.0.1:8000`, preserving same-origin cookie behavior seamlessly.
  - *CORS & CSRF*: `django-cors-headers` configured with `CORS_ALLOW_CREDENTIALS = True`, `CSRF_TRUSTED_ORIGINS`, and `SESSION_COOKIE_SAMESITE = 'Lax'`.
  - *Production*: Same-origin deployment or secure domain cookie sharing with HTTPS and `SESSION_COOKIE_SECURE = True`.
- **Test User Provisioning**: Standard Django seed script / management command (`python manage.py seed_catalog`) provisions test accounts without hardcoded named user assumptions in core code.

---

### 2.8 UI & UX Principles [APPROVED]
- Dark-mode pop-culture media platform aesthetic (`#0b0c10` / `#121318` theme).
- Poster-dense grid layouts with clean typography and strong visual hierarchy.
- Compact data presentation with hover quick-actions.
- Responsive design supporting desktop, tablet, and mobile browsers.
- Visually distinctive DreamTeal reaction badge styling across cards, details, profiles, and diary history.
- No gaudy purple neon, overused glassmorphism, or empty AI dashboard layouts.
