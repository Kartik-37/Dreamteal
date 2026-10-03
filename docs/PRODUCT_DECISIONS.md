# DreamTeal Architectural & Product Decisions Log

This file records key decisions made during the design and development of DreamTeal. Every architectural or product choice must be documented here to preserve context and avoid regressions.

---

## Decision Log

### DEC-001: Absolute Exclusion of Star Ratings
- **Date**: 2026-10-03
- **Status**: APPROVED
- **Context**: Standard media tracking platforms rely heavily on 1-to-5 or 1-to-10 star ratings.
- **Decision**: Remove star ratings entirely across the application (models, serializers, frontend UI, filters, sorting, and recommendation calculations).
- **Rationale**: The user explicitly requested a qualitative reaction-badge system over traditional numeric star ratings.

---

### DEC-002: Separation of Status, Progress, Diary Log, and Review Entities
- **Date**: 2026-10-03
- **Status**: APPROVED
- **Context**: Forcing media tracking into a single flat model loses historical diary records and confuses current status with past reviews.
- **Decision**: Architect five separate entities:
  1. `MediaItem` (Catalog representation)
  2. `UserMediaStatus` (Current relationship state: e.g. `Watching`, `Completed`, `Backlog`)
  3. `UserMediaProgress` (Current quantitative progress position)
  4. `DiaryLog` (History-preserving diary records that users can edit through controlled log editing)
  5. `MediaReview` (Qualitative reaction badge + written review text)
- **Rationale**: Prevents data loss during rewatches/re-reads and supports accurate media progress and historical tracking.

---

### DEC-003: Multi-Category Media Catalog Architecture (Polymorphic / Extension Pattern)
- **Date**: 2026-10-03
- **Status**: PROPOSED
- **Context**: Movies, TV Series, Manga, and Games have different attributes (e.g. game platforms vs. manga chapters vs. movie runtimes).
- **Decision**: Use a shared base `MediaItem` model for common metadata (title, slug, synopsis, poster, release year, genres, tags) coupled with dedicated extension models (`MovieDetail`, `SeriesDetail`, `MangaDetail`, `GameDetail`).
- **Rationale**: Keeps database queries clean, supports type-specific fields without null clutter, and allows seamless future PostgreSQL migration.

---

### DEC-004: Deterministic Recommendation Engine Architecture
- **Date**: 2026-10-03
- **Status**: APPROVED (Exact Scoring Formula: PROVISIONAL | Weights: NOT FINALIZED)
- **Context**: AI/ML recommendation engines add complexity and risk producing hallucinated recommendations.
- **Decision**: Build a deterministic rule-based engine relying on shared genres, cross-category theme/vibe tags, and user reaction history. The architecture is approved, while the exact mathematical formula and numeric weightings ($w_g, w_t, w_c, w_r$) remain provisional and subject to tuning.
- **Rationale**: Guarantees predictable, auditable recommendations within the user's catalog.

---

### DEC-005: Visual Identity & UX Standard
- **Date**: 2026-10-03
- **Status**: APPROVED
- **Context**: The app should take inspiration from Moctale and Letterboxd without cloning them or feeling like generic AI-generated dark templates.
- **Decision**: Establish a high-density, dark pop-culture aesthetic with dark neutral backgrounds (`#0b0c10`), poster-first layout grids, crisp typography, and functional hover overlays.
- **Rationale**: Delivers a premium, custom platform feel with purpose-driven UX.

---

### DEC-006: Universal Qualitative Reaction-Based Review System
- **Date**: 2026-10-03
- **Status**: APPROVED
- **Context**: Need for an intuitive, non-numeric review system with DreamTeal's unique brand identity across Movies, TV Series, Manga, Manhwa/Webtoons, and Video Games.
- **Decision**: Adopt ONE universal qualitative reaction taxonomy:
  1. **Peak** (exceptional experience, strongly recommended - Electric Gold)
  2. **Loved It** (genuinely enjoyable, highly valued - Warm Coral)
  3. **Good Time** (enjoyable and worth experiencing, but not exceptional - Radiant Teal)
  4. **Not My Thing** (did not connect, even if media has strengths - Muted Lavender)
  5. **Skip** (would not recommend spending time on - Crimson)
  - Implemented via dynamic `ReactionDefinition` models seeded via controlled seed data.
  - Strictly qualitative: NOT hidden numeric ratings, NOT internally mapped to stars, NO numerical equivalents, NOT described as a "5-star alternative".
  - Visually represented through custom typography, color tokens, and text labels. No emoji, no icons, and no generic icon sets. Text labels are always shown.
- **Rationale**: Replaces obsolete star ratings with meaningful qualitative verdicts that express authentic audience appreciation.

---

### DEC-007: Django Session Authentication & CSRF Architecture
- **Date**: 2026-10-03
- **Status**: APPROVED
- **Context**: Authentication and secure state management between the Django backend and React frontend.
- **Decision**: Use standard Django Session Authentication (`django.contrib.auth.models.User`) and CSRF protection. Do not introduce JWT. React frontend communicates via session cookies (`sessionid`) and `csrftoken`. For local Vite development, use Vite's built-in proxy to route `/api/` to Django, ensuring seamless same-origin cookie exchange. Test users provisioned via management commands.
- **Rationale**: Simplifies security, leverages battle-tested Django sessions and CSRF defenses, and avoids the token refresh complexities of JWT.

---

### DEC-008: History-Preserving Diary Records with Controlled Editing
- **Date**: 2026-10-03
- **Status**: APPROVED
- **Context**: The Letterboxd-style diary experience requires users to record each consumption event while having the ability to edit mistakes in their log entries.
- **Decision**: Diary entries (`DiaryLog`) are history-preserving records that users can edit via controlled log editing (updating date, session notes, progress snapshot, rewatch flag). Individual diary records remain distinct rows. Rewatches/re-reads/replays create new discrete diary entries rather than overwriting historical records. Deletion removes only that specific entry.
- **Rationale**: Fully supports Letterboxd-style rewatch timelines without data loss or historical entry clobbering.

---

### DEC-009: Category-Specific Progress Tracking Architecture
- **Date**: 2026-10-03
- **Status**: APPROVED
- **Context**: Progress tracking attributes differ drastically across media types (Series: season/episode; Manga: chapter/volume; Games: hours played/completion type; Movies: watched status).
- **Decision**: Decompose user progress into category-specific extension models:
  ```text
  UserMediaProgress (Base)
      ├── SeriesProgress (current_season, current_episode, last_watched_episode_title)
      ├── MangaProgress (current_chapter, current_volume)
      └── GameProgress (hours_played, completion_type, platform_played_on)
  ```
  Movies do not require a progress extension unless future requirements introduce one.
- **Rationale**: Directly mirrors the approved Media Catalog extension pattern, eliminates null column clutter, and enforces database-level type validation.

---

### DEC-010: Automatic Diary → Progress Synchronization
- **Date**: 2026-10-03
- **Status**: APPROVED
- **Context**: Keeping active progress in sync when logging diary consumption events without corrupting historical records.
- **Decision**:
  1. Default behavior is automatic synchronization: creating a diary entry automatically advances current progress forward.
  2. Historical non-reversal rule: logging a historical entry (e.g. logging Season 2 Episode 4 when current is Season 2 Episode 8) saves the diary record but does NOT regress current progress.
  3. Manga reading advances forward to the logged chapter.
  4. Video game hours accumulate additively (`hours_played += session_hours`), and completion type updates upon finishing.
  5. UI/API provides an optional opt-out flag (`sync_progress: false`) for edge cases.
- **Rationale**: Streamlines the primary logging UX while strictly protecting active progress integrity against retrospective diary additions.

---

### DEC-011: Backend-Only External Provider Adapter Architecture
- **Date**: 2026-10-03
- **Status**: APPROVED
- **Context**: Ingesting and discovering real-world Movie, Series, Manga, Manhwa, and Game metadata while protecting user privacy and preventing external API key exposure.
- **Decision**:
  1. Frontend (React) NEVER calls third-party APIs directly. All requests flow through Django REST API -> Service Layer -> Provider Adapters.
  2. Implement an extensible `BaseMetadataProvider` interface with initial adapters: TMDB (Movies, TV Series), AniList (Manga/Manhwa), Jikan (Manga fallback), RAWG (Video Games).
  3. Relational mapping through `ExternalProvider` and `ExternalMediaMapping` with unique constraint on `(provider, external_id)`.
  4. Data-driven legal attribution notices for all providers.
  5. Zero-star guarantee: NEVER import external numeric ratings or convert them to DreamTeal reactions.
  6. Provider sync NEVER overwrites user tracking, progress, diary logs, or reviews.
- **Rationale**: Keeps provider APIs isolated, enables smooth addition of future providers, enforces deduplication, and secures all credentials server-side.

---

### DEC-012: Provider Discovery Semantics, Cross-Provider Deduplication, Region Settings & Test Isolation
- **Date**: 2026-10-03
- **Status**: APPROVED
- **Context**: Corrections to Phase 2 to ensure accurate discovery semantics, prevent cross-provider catalog duplication, regionalize OTT watch providers, and enforce 100% offline unit tests.
- **Decision**:
  1. **Discovery Semantics**: Strictly differentiate between `latest` (actual new releases/airing), `popular` (sustained engagement), `trending` (weekly momentum), and `upcoming` (scheduled unreleased). Where a provider lacks native trending (Jikan, RAWG), gracefully fallback to popular with clear documentation.
  2. **Cross-Provider Deduplication**: Use `MediaMatcherService` with multi-signal confidence scoring ($\ge 75.0$ threshold based on title, release year penalty/boost, creator matching, and AniList `idMal` bridging). Merges external mappings onto the single existing `MediaItem` without creating duplicate catalog records.
  3. **AniList $\rightarrow$ Jikan Fallback**: Never pass AniList IDs directly to Jikan. Require normalized title matching with confidence validation; otherwise return controlled fallback unavailable.
  4. **Regional Watch Providers**: Introduce configurable `DEFAULT_PROVIDER_REGION=IN` (defaulting to India) without hardcoded countries or arbitrary random region fallbacks.
  5. **Import HTTP Status**: Return `201 Created` for brand new catalog items, `200 OK` for existing/refreshed items.
  6. **Universal Search Distribution**: Use balanced round-robin category interleaving across Movies, Series, Manga, and Games when no category is specified.
  7. **100% Offline Test Suite**: All tests in `python manage.py test` must be 100% mocked and offline; live network reachability is isolated into the optional `python manage.py test_external_providers` command.
- **Rationale**: Prevents data corruption, ensures accurate discovery semantics, eliminates test flakiness, and optimizes search fairness across media categories.

---

### DEC-013: Canonical Provider Identity, Metadata Ownership Boundaries, Game Hours Lifecycle & Privacy Controls
- **Date**: 2026-10-03
- **Status**: APPROVED
- **Context**: Final Phase 2 correction pass to remove legacy direct provider fields, define clear catalog metadata sync boundaries, ensure transaction-safe game hours lifecycle, enforce private review security, and validate seed data.
- **Decision**:
  1. **Canonical Provider Identity**: Completely remove legacy `tmdb_id`, `mal_id`, `rawg_id` fields from `MediaItem`. All provider identity is stored canonically in `ExternalProvider` and `ExternalMediaMapping`.
  2. **Metadata Ownership Boundaries**: Provider synchronization (`force_refresh=True`) updates provider-owned fields (`title`, `synopsis`, `release_year`, `poster_image_url`, `backdrop_image_url`, detail models) and reconciles provider-supplied taxonomy (`genres`, `tags`). User-owned tracking, progress, diary logs, reviews, and collections are strictly immutable to provider sync.
  3. **Manga vs Manhwa Subtypes**: DreamTeal maintains `MANGA` as the single canonical local media type, using `MangaDetail.manga_type` for subtype differentiation (`MANGA`, `MANHWA`, `MANHUA`, `WEBTOON`). AniList and Jikan adapters pass subtype filters (`countryOfOrigin: "KR"` / `type=manhwa`) to return authentic Manhwa results.
  4. **Game Diary Hours Lifecycle**: Diary sessions are the source of truth for session gameplay. `GameProgress.hours_played` is maintained consistently through transaction-safe hooks on creation, edit (delta calculation), deletion (deducting synced session hours), and is unaffected when `sync_progress=False`.
  5. **Review Privacy & Scoping**: Private reviews (`is_public=False`) are visible only to the owner (404 Not Found for anonymous and non-owning authenticated users). All user tracking endpoints (status, progress, diary logs) strictly filter querysets by the authenticated user.
  6. **Seed Data Integrity**: Seed data binds verified provider IDs (e.g. Cyberpunk 2077 -> RAWG 41494 `cyberpunk-2077`) and executes validation on seed to prevent invalid bindings.
  7. **Safe Environment Management**: Configuration loads automatically via `python-dotenv`. Hard-coded fallback secrets are banned; production startup without `SECRET_KEY` fails immediately with `ImproperlyConfigured`.
- **Rationale**: Eliminates legacy redundant schema columns, guarantees data integrity across game tracking, protects user privacy, and ensures clean environment configuration.



