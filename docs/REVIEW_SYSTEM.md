# DreamTeal Reaction-Based Review Architecture

## 1. Concept & Requirements
DreamTeal uses a **non-numeric qualitative reaction model** instead of traditional star ratings.

### Core Principles:
- **Zero Star Ratings [APPROVED]**: No 1–5 star icons, no decimal star numbers (0.5–5.0), no ratings out of 10, and no average numerical rating scores across the database, API, or UI.
- **Universal Reaction System [APPROVED]**: ONE universal qualitative reaction system applied uniformly across Movies, TV Series, Manga, Manhwa/Webtoons, and Video Games.
- **Strictly Qualitative [APPROVED]**:
  - Reactions are qualitative verdicts, NOT hidden numeric ratings.
  - Do NOT internally map reactions to stars (e.g. Peak != 5 stars, Skip != 1 star).
  - Do NOT display numerical equivalents anywhere.
  - Do NOT describe the system as a "5-star alternative".
- **Visual Identity**: Represented through distinctive DreamTeal color tokens, uppercase typography, and text labels. No emoji, no icons, and no generic icon sets are used. Text labels are always shown.
- **Separation from Diary Logging [APPROVED]**:
  - Diary Log = *"I consumed this on this date."*
  - Review / Reaction = *"This is how I feel about this media."*
  - These concepts remain completely distinct database entities. A user can log viewing activity without reviewing, or review without logging every viewing.

---

## 2. Approved Reaction Taxonomy [APPROVED]

| Reaction Label | Reaction Key | Editorial Definition | Visual Color Identity |
| :--- | :--- | :--- | :--- |
| **Peak** | `peak` | An exceptional experience that the user strongly recommends. | Electric Gold (`--reaction-peak-color`: `#f59e0b`) |
| **Loved It** | `loved_it` | A genuinely enjoyable experience that the user highly values. | Warm Coral (`--reaction-loved-it-color`: `#fb7185`) |
| **Good Time** | `good_time` | Enjoyable and worth experiencing, but not exceptional. | Radiant Teal (`--reaction-good-time-color`: `#14b8a6`) |
| **Not My Thing** | `not_my_thing` | The user did not connect with it, even if the media may have strengths. | Muted Lavender (`--reaction-not-my-thing-color`: `#a78bfa`) |
| **Skip** | `skip` | The user would not recommend spending time on it. | Crimson (`--reaction-skip-color`: `#e11d48`) |

---

## 3. Data Model Architecture

### 3.1 Dynamic Reaction Definition (`ReactionDefinition`)
To prevent hardcoded choices in model columns and preserve database flexibility, reaction definitions are stored in the database and seeded through controlled seed data:
- `key`: Unique slug identifier (`"peak"`, `"loved_it"`, etc.)
- `display_name`: Human-readable label
- `description`: Official editorial guidance
- `active`: Boolean flag
- `sort_order`: Display sequence (1 to 5)

### 3.2 Review Entity (`MediaReview`)
- `user`: Foreign Key to `User`
- `media_item`: Foreign Key to `MediaItem`
- `reaction`: Foreign Key to `ReactionDefinition` (nullable if review is text-only, or populated with the selected verdict)
- `review_text`: User critique (Markdown enabled)
- `contains_spoilers`: Spoiler mask flag
- `is_public`: Visibility toggle
- `created_at` & `updated_at`: Audit timestamps
- *Constraint*: `UniqueTogether(user, media_item)` — One active review/reaction per user per media item.

---

## 4. Review Lifecycle & RESTful Operations (Strict Create vs Update)

- **Creation (`POST /api/v1/reviews/`)**:
  - Creates the review for the user and media item.
  - Enforces `UniqueTogether(user, media_item)`.
  - Returns `201 Created` or `409 Conflict` if a review already exists.
- **Editing (`PATCH /api/v1/reviews/<id>/`)**:
  - Updates review text, reaction badge, spoiler setting, or visibility.
  - Never mutates historical diary log entries.
- **Deletion (`DELETE /api/v1/reviews/<id>/`)**:
  - Removes the review without affecting the user's historical diary logs or catalog items.
