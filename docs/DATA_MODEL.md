# DreamTeal Data Model Specification

This document details the database schema entities for DreamTeal. Star ratings and numeric equivalents are strictly absent across all entities.

---

## 1. Core Catalog Entities

### `Genre`
- `id` (UUID / Auto)
- `name` (String, unique)
- `slug` (String, unique)

### `Tag` (Vibe / Theme / Keywords)
- `id` (UUID / Auto)
- `name` (String, e.g. "Cyberpunk", "Dark Fantasy", "Mind-Bending", "Cozy")
- `slug` (String, unique)

### `MediaItem` (Base Catalog Model)
- `id` (UUID)
- `media_type` (Enum: `MOVIE`, `SERIES`, `MANGA`, `GAME`)
- `title` (String)
- `slug` (String, unique)
- `synopsis` (Text)
- `release_year` (Integer)
- `poster_url` (URL/Image)
- `backdrop_url` (URL/Image, optional)
- `genres` (ManyToMany -> Genre)
- `tags` (ManyToMany -> Tag)
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

---

## 2. Media-Type Extension Entities (Catalog)

### `MovieDetail`
- `media_item` (OneToOne -> MediaItem, primary_key)
- `director` (String)
- `runtime_minutes` (Integer)
- `studio` (String)
- `ott_providers` (JSON / ManyToMany: e.g. Netflix, Prime Video)

### `SeriesDetail`
- `media_item` (OneToOne -> MediaItem, primary_key)
- `creators` (String)
- `total_seasons` (Integer)
- `total_episodes` (Integer)
- `status` (Enum: `AIRING`, `ENDED`, `CANCELLED`)
- `ott_providers` (JSON / ManyToMany)

### `MangaDetail`
- `media_item` (OneToOne -> MediaItem, primary_key)
- `author` (String)
- `artist` (String)
- `manga_type` (Enum: `MANGA`, `MANHWA`, `MANHUA`, `WEBTOON`)
- `status` (Enum: `PUBLISHING`, `FINISHED`, `HIATUS`)
- `total_chapters` (Integer, nullable if ongoing)

### `GameDetail`
- `media_item` (OneToOne -> MediaItem, primary_key)
- `developer` (String)
- `publisher` (String)
- `platforms` (JSON Array: e.g. `["PC", "PS5", "Switch"]`)
- `average_story_hours` (Float, optional)

---

## 3. User Tracking & Category-Specific Progress Entities [APPROVED]

### `UserMediaStatus` (Current State)
- `id` (UUID)
- `user` (ForeignKey -> User, on_delete=CASCADE)
- `media_item` (ForeignKey -> MediaItem, on_delete=CASCADE)
- `status` (Enum per category):
  - Movies: `PLAN_TO_WATCH`, `WATCHING`, `WATCHED`, `DROPPED`
  - Series: `PLAN_TO_WATCH`, `WATCHING`, `COMPLETED`, `PAUSED`, `DROPPED`
  - Manga: `PLAN_TO_READ`, `READING`, `COMPLETED`, `PAUSED`, `DROPPED`
  - Games: `BACKLOG`, `PLAYING`, `FINISHED`, `PAUSED`, `ABANDONED`
- `is_favorite` (Boolean, default False)
- `created_at` (Timestamp)
- `updated_at` (Timestamp)
- *Constraint*: `UniqueTogether(user, media_item)`

---

### Category-Specific Progress Architecture [APPROVED]

To maintain strict domain cleanliness and avoid sparse, invalid columns (e.g. game hours on manga), progress is architected using a base model with category-specific extension models:

```text
UserMediaProgress (Base)
    ├── SeriesProgress (TV Series progress)
    ├── MangaProgress (Manga/Manhwa reading progress)
    └── GameProgress (Video game gameplay progress)
```
*Note: Movies do not require a category-specific progress extension unless future requirements introduce one.*

#### `UserMediaProgress` (Base Progress Tracker)
- `id` (UUID)
- `user` (ForeignKey -> User, on_delete=CASCADE)
- `media_item` (ForeignKey -> MediaItem, on_delete=CASCADE)
- `created_at` (Timestamp)
- `updated_at` (Timestamp)
- *Constraint*: `UniqueTogether(user, media_item)`

#### `SeriesProgress`
- `id` (UUID)
- `progress` (OneToOne -> UserMediaProgress, on_delete=CASCADE, related_name='series_progress')
- `current_season` (PositiveIntegerField, default=1)
- `current_episode` (PositiveIntegerField, default=0)
- `last_watched_episode_title` (String, max_length=255, blank=True)

#### `MangaProgress`
- `id` (UUID)
- `progress` (OneToOne -> UserMediaProgress, on_delete=CASCADE, related_name='manga_progress')
- `current_chapter` (PositiveIntegerField, default=0)
- `current_volume` (PositiveIntegerField, default=0, null=True, blank=True)

#### `GameProgress`
- `id` (UUID)
- `progress` (OneToOne -> UserMediaProgress, on_delete=CASCADE, related_name='game_progress')
- `hours_played` (DecimalField/FloatField, max_digits=6, decimal_places=1, default=0.0)
- `completion_type` (Enum: `MAIN_STORY`, `MAIN_EXTRA`, `COMPLETIONIST`, null=True, blank=True)
- `platform_played_on` (String, max_length=100, blank=True)

---

## 4. History-Preserving Diary & Universal Reaction Entities [APPROVED]

### `DiaryLog` (History-Preserving Diary Records with Controlled Editing) [APPROVED]
- **Concept**: Represents consumption events at specific dates: *"I consumed this on this date."*
- **Fields**:
  - `id` (UUID, primary key)
  - `user` (ForeignKey -> User, on_delete=CASCADE)
  - `media_item` (ForeignKey -> MediaItem, on_delete=CASCADE)
  - `logged_date` (Date, default `today`) — *Editable*
  - `is_rewatch_or_replay` (Boolean, default False) — *Editable*
  - `session_notes` (Text, optional user thought/quick note for this session) — *Editable*
  - `progress_snapshot` (JSON: e.g. `{"season": 2, "episode": 5}`, `{"chapter": 142}`, or `{"hours_spent": 3.5}`) — *Editable*
  - `created_at` (Timestamp, set once on creation) — *Immutable audit timestamp*
  - `updated_at` (Timestamp, updated whenever edited)

#### Automatic Diary → Progress Synchronization Rules [APPROVED]:
1. **Default Synchronization**: Creating a diary log automatically advances active progress forward.
2. **Forward Progress Rule**:
   - Series: Current S2E3 + Diary S2E4 $\rightarrow$ Current becomes S2E4.
   - Manga: Current Chapter 80 + Diary Chapter 84 $\rightarrow$ Current becomes Chapter 84.
   - Games: Current 12.0 hrs + Diary 2.5 hrs session $\rightarrow$ Current becomes 14.5 hrs.
3. **Historical Non-Reversal Rule**:
   - Historical entries NEVER move active progress backwards.
   - Example: Current is Season 2 Episode 8; retrospective diary logged for Season 2 Episode 4 $\rightarrow$ Diary entry saved as Episode 4, Current remains Episode 8.
   - Example: Current is Chapter 84; retrospective diary logged for Chapter 70 $\rightarrow$ Diary entry saved as Chapter 70, Current remains 84.
4. **Game Completion Rules**:
   - Logging a game session adds to `hours_played`.
   - If the log specifies completion (`completion_type`), `GameProgress.completion_type` is set and `UserMediaStatus` can transition to `Finished`.
5. **Opt-Out Control**:
   - The API and UI support `sync_progress: false` to allow recording an isolated session without affecting active progress, but `sync_progress: true` is the default.

---

### `ReactionDefinition` (Dynamic Qualitative Reaction Badges) [APPROVED]
- **Concept**: Qualitative verdicts replacing star ratings across all media categories. Badges are stored dynamically in the database and seeded through controlled seed data.
- **Fields**:
  - `id` (UUID / Auto)
  - `key` (String, unique slug identifier)
  - `display_name` (String, human-readable label)
  - `description` (Text, editorial meaning of this verdict)
  - `active` (Boolean, default True)
  - `sort_order` (Integer, order in the UI picker)

#### Approved Universal Reaction Seed Taxonomy:
| Key | Display Name | Visual Color Token | Description | Sort Order |
| :--- | :--- | :--- | :--- | :---: |
| `peak` | **Peak** | Electric Gold (`--reaction-peak`) | An exceptional experience that the user strongly recommends. | 1 |
| `loved_it` | **Loved It** | Warm Coral (`--reaction-loved-it`) | A genuinely enjoyable experience that the user highly values. | 2 |
| `good_time` | **Good Time** | Radiant Teal (`--reaction-good-time`) | Enjoyable and worth experiencing, but not exceptional. | 3 |
| `not_my_thing` | **Not My Thing** | Muted Lavender (`--reaction-not-my-thing`) | The user did not connect with it, even if the media may have strengths. | 4 |
| `skip` | **Skip** | Crimson (`--reaction-skip`) | The user would not recommend spending time on it. | 5 |

*Critical Rules*:
- Strictly qualitative: NOT hidden numeric ratings, NOT mapped to 1–5 stars, NO numerical equivalents.
- Universal across Movies, TV Series, Manga, Manhwa/Webtoons, and Video Games.
- **No Emoji or Icons**: Reaction badges rely on dedicated typography, text labels, and color design tokens. No emojis or generic icon sets are stored or required. Text labels are always shown; color is never the sole indicator of meaning.

---

### `MediaReview` (Qualitative Reaction & Written Review) [APPROVED]
- **Concept**: Represents the user's critique/verdict: *"This is how I feel about this media."*
- **Fields**:
  - `id` (UUID)
  - `user` (ForeignKey -> User, on_delete=CASCADE)
  - `media_item` (ForeignKey -> MediaItem, on_delete=CASCADE)
  - `reaction` (ForeignKey -> ReactionDefinition, on_delete=SET_NULL, null=True, blank=True)
  - `review_text` (Text, optional written critique, supports Markdown)
  - `contains_spoilers` (Boolean, default False)
  - `is_public` (Boolean, default True)
  - `created_at` (Timestamp)
  - `updated_at` (Timestamp)
- *Constraint*: `UniqueTogether(user, media_item)` (one active review per user per media item)

---

## 5. User & Multi-User Architecture Entities [APPROVED]

### Standard Django User (`django.contrib.auth.models.User`)
- Standard Django user authentication with username, email, password hashing, and permissions.
- Authenticated via standard Django session cookies with CSRF defense.

### `UserProfile`
- `id` (UUID)
- `user` (OneToOne -> User, on_delete=CASCADE, related_name='profile')
- `display_name` (String, max_length=150, blank=True)
- `bio` (Text, blank=True)
- `avatar_url` (URLField/Image, blank=True)
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

---

## 6. External Metadata Provider & Mapping Entities [APPROVED]

### `ExternalProvider`
- `id` (UUID)
- `provider_key` (SlugField, unique, e.g. `'tmdb'`, `'anilist'`, `'jikan'`, `'rawg'`)
- `display_name` (CharField, e.g. `'TMDB'`, `'AniList'`, `'Jikan (MyAnimeList)'`, `'RAWG'`)
- `base_url` (URLField)
- `attribution_text` (TextField, mandatory legal notice per provider terms)
- `attribution_url` (URLField)
- `active` (BooleanField, default=True)

### `ExternalMediaMapping`
- `id` (UUID)
- `media_item` (ForeignKey -> MediaItem, on_delete=CASCADE, related_name='external_mappings')
- `provider` (ForeignKey -> ExternalProvider, on_delete=CASCADE, related_name='mappings')
- `external_id` (CharField, max_length=100, db_index=True)
- `external_url` (URLField, direct URL to item on provider's site)
- `last_synced_at` (DateTimeField, auto_now=True)
- `source_updated_at` (DateTimeField, null=True, blank=True)
- *Constraints*: `UniqueConstraint(fields=['provider', 'external_id'])` — guarantees one-to-one mapping per provider ID.
- *Cross-Provider Deduplication*: Multiple mappings (e.g. AniList and Jikan) can point to the same `MediaItem` via `MediaMatcherService` confidence matching.

---

## 7. Metadata Ownership Boundaries & Invariants [APPROVED]

### Architectural Ownership Matrix
To guarantee user data immutability and predictable catalog synchronization, DreamTeal strictly delineates field ownership:

| Tier | Controlled Models / Fields | Synchronization Behavior (`force_refresh=True`) | User Modification Rules |
| :--- | :--- | :--- | :--- |
| **Provider-Owned Catalog** | `MediaItem.title`, `synopsis`, `release_year`, `poster_image_url`, `backdrop_image_url`, `genres`, `tags`, detail extensions (`MovieDetail`, `SeriesDetail`, `MangaDetail`, `GameDetail`), `ExternalMediaMapping` | Updated directly from incoming provider payload. Provider-supplied genres and tags are reconciled. | Read-only in regular client workflows; curated via administrative or catalog provider imports. |
| **DreamTeal Platform Catalog** | `MediaItem.slug`, `media_type`, `created_at`, `updated_at` | Immutable once created. Preserves permanent URL slug routes and canonical media type. | Managed internally by Django lifecycle. |
| **User-Owned Tracking & Engagement** | `UserMediaStatus`, `UserMediaProgress`, `SeriesProgress`, `MangaProgress`, `GameProgress`, `DiaryLog`, `MediaReview`, `Collection`, `CollectionItem` | **STRICTLY IMMUTABLE** to provider ingestion. Provider sync cannot modify, overwrite, or delete any user record. | Full CRUD by authenticated record owner with strict user-scoping and privacy controls. |

### Game Diary Hours Aggregation Lifecycle
1. **Source of Truth**: `DiaryLog` consumption entries are the transactional source of truth for session-based gameplay.
2. **Aggregated Total**: `GameProgress.hours_played` aggregates cumulative investment across sessions.
3. **Internal Sync Tracking**: The synced session duration is recorded in `progress_snapshot['_synced_hours']`.
4. **Lifecycle Hooks**:
   - **Creation**: When created with `sync_progress=True`, `session_hours` is atomically added to `GameProgress.hours_played`.
   - **Editing**: When session hours are updated (e.g., 2.5h -> 5.0h), the difference (`+2.5h`) is applied atomically without double-counting.
   - **Deletion**: When a synced session log is deleted, its synced hours are deducted from `GameProgress.hours_played` (floored at 0.0).
   - **Sync Suppression (`sync_progress=False`)**: When a log is saved with `sync_progress=False`, hours are recorded as unsynced (`_synced_hours = '0.0'`) and do not alter `GameProgress` on creation, update, or deletion.

---

## 8. Recommendation Engine Data Architecture [APPROVED]

### 8.1 Zero Schema Additions
Phase 3 introduces **no new database models, tables, or schema migrations**. The engine operates entirely on top of the established canonical schema:
- **Catalog Metadata**: `MediaItem`, `Genre`, `Tag`, `MovieDetail`, `SeriesDetail`, `MangaDetail`, `GameDetail`.
- **User Engagement & Tracking**: `UserMediaStatus`, `DiaryLog`.
- **User Qualitative Reviews**: `MediaReview`, `ReactionDefinition`.
- **Cross-Provider Mappings**: `ExternalMediaMapping` (deduplication & candidate canonicalization).

### 8.2 In-Memory Scored Result Dataclass
The recommendation engine uses an internal, typed dataclass to compute deterministic scores before passing results to the presentation/serializer layer:

```python
@dataclass
class ScoredRecommendation:
    candidate: MediaItem
    total_score: float
    tag_score: float
    genre_score: float
    cross_media_score: float
    affinity_score: float
    match_reasons: list[str]
    shared_tags: list[str]
    shared_genres: list[str]
    is_franchise_linked: bool
```

This guarantees complete isolation between internal similarity computation and external JSON representation, ensuring no internal scores or floating-point weights are exposed to clients by default.
