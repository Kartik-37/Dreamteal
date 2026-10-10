# DreamTeal Project Changelog

All notable changes to the DreamTeal project specifications and codebase will be documented in this file.

---

## [0.4.3-alpha] - 2026-10-10
### Changed & Fixed (Phase 2 Repository Integrity & Final Audit)
- **Git Merge Conflict Resolution**: Reconstructed clean `README.md` removing conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`); removed absolute `file:///` links across `README.md` and `PROJECT_CONTEXT.md` in favor of relative links.
- **Centralized Game Session Service**: Implemented `GameSessionTrackingService` in `apps/tracking/services.py`; routed all diary session additions, edits, and deletions (including bulk queryset deletions) through the service to keep `GameProgress.hours_played` consistent without double-counting.
- **Progress Validation & Bounds Enforcement**: Added strict category validation in `UserMediaProgressSerializer` rejecting incompatible nested progress types (e.g. series progress on manga); added numeric range validations (rejecting negative chapters, episodes, and hours); prevented tampering with internal `_synced_hours`.
- **Contract & Serializer Bidirectional Aliasing**: Supported `media_id` vs `media_item` and `reaction_key` vs `reaction` seamlessly across request validation, response serialization, and query parameter filtering.
- **Manga / Manhwa Uncertainty Preservation**: Maintained uncertainty (`subtype=None`) when metadata origin/format is ambiguous rather than inventing a subtype; verified cross-provider matching threshold ($\ge 75.0$) preventing improper automatic merges.
- **Session Authentication & CSRF Enforcement**: Verified CSRF protection on unsafe session-authenticated requests using `APIClient(enforce_csrf_checks=True)`; verified strict review privacy for anonymous users, owners, and non-owners across detail and list views.
- **Automated Verification**: Expanded test suite to **88 automated tests** passing 100% offline and deterministic in ~71s.

---

## [0.4.2-alpha] - 2026-10-03
### Changed & Fixed (Phase 2 Final Correction Pass)
- **Canonical Provider Identity**: Completely removed legacy provider fields (`tmdb_id`, `mal_id`, `rawg_id`) from `MediaItem`. All third-party identity is now stored exclusively in `ExternalProvider` and `ExternalMediaMapping` (Migration `0003`). Added regression test asserting no legacy provider ID fields exist on `MediaItem`.
- **Automatic .env Loading & Secret Key Security**: Added `python-dotenv==1.0.1` to `requirements.txt` and integrated `load_dotenv()` into `dreamteal/settings.py`. Removed hardcoded `SECRET_KEY` fallback; when `DEBUG=False`, startup raises `ImproperlyConfigured` if `SECRET_KEY` is missing, empty, or insecure. Added validation for `ALLOWED_HOSTS`.
- **True Manga vs Manhwa Discovery & Search**: Filtered AniList queries with `countryOfOrigin: "KR"` (for Manhwa) and `"JP"` (for Manga), and Jikan queries with `type: "manhwa"` / `"manga"`. Mapped external results to `NormalizedSearchResult.subtype` while preserving DreamTeal's single local `MediaItem.media_type = MANGA` and storing specific format in `MangaDetail.manga_type`.
- **Provider Metadata Refresh & Taxonomy Reconciliation**: On `force_refresh=True`, provider-owned catalog metadata (title, synopsis, release year, poster/backdrop URLs, detail extensions) are updated with latest provider data. Provider taxonomy (`genres`, `tags`) is reconciled via set assignment without mutating user-owned data.
- **Seed Data Provider Verification & Validation**: Corrected Cyberpunk 2077 RAWG external ID to `41494` (`cyberpunk-2077`). Added an automated seed verification step to `seed_catalog` ensuring mapped titles match expected provider records.
- **AniList $\rightarrow$ Jikan Import Fallback**: Integrated `title_hint` into `registry.import_media()` and `fetch_details()`. When AniList details are unavailable, queries Jikan search using `title_hint`, scores candidate similarity using `MediaMatcherService`, and binds details if confidence $\ge 75.0\%$.
- **Transaction-Safe Game Playtime Aggregation**: Made `DiaryLog` the transactional source of truth for session playtime. Accurately maintains `GameProgress.hours_played` on session creation, update (computing delta), deletion (deducting synced hours), and isolates sessions with `sync_progress=False`.
- **Review Privacy & Scoped Querysets**: Enforced private review access controls (`404 Not Found` for anonymous or non-owning authenticated users). Scoped `UserMediaStatus`, `UserMediaProgress`, and `DiaryLog` detail and list views strictly to the authenticated user.
- **Provider Active State Routing**: Added database-driven check `ProviderRegistry.is_provider_active(provider_key)` using `ExternalProvider.active` to avoid routing search, discovery, or imports to deactivated providers.
- **Comprehensive Automated Tests**: Added 16 new automated tests bringing the total test suite to 72 tests passing with 100% offline mocks.

---

## [0.4.1-alpha] - 2026-10-03
### Changed & Fixed (Phase 2 Correction Pass)
- **Discovery Semantics Refinement**: Differentiated between `popular`, `latest`, `trending`, and `upcoming` feeds across TMDB, AniList, Jikan, and RAWG. Where providers lack native trending (Jikan, RAWG), documented transparent fallback to popular instead of fabricating scores.
- **AniList $\rightarrow$ Jikan Fallback**: Solved identifier mismatch between AniList and MyAnimeList/Jikan IDs. Implemented safe title-normalized candidate searching with confidence scoring and AniList `idMal` bridging; never passes AniList IDs directly to Jikan.
- **Safe Cross-Provider Deduplication**: Created `MediaMatcherService` with multi-signal confidence scoring ($\ge 75.0$ threshold) evaluating media type, title/alt-titles, release year penalties/boosts, and creator overlap. Confidently links multi-source items (e.g. AniList and Jikan for *Solo Leveling*) to a single `MediaItem` without duplicating catalog records.
- **Region-Aware TMDB Watch Providers**: Added configurable `DEFAULT_PROVIDER_REGION=IN` (defaulting to India). Avoids hardcoded countries and strictly eliminates arbitrary random region fallbacks when regional data is absent.
- **Media Import HTTP Status Codes**: Updated `POST /api/v1/media/import/` to return `201 Created` when a new `MediaItem` is generated and `200 OK` when an existing/deduplicated record is returned or refreshed.
- **Balanced Universal Search Interleaving**: Replaced naive result slicing with round-robin interleaving across Movie, Series, Manga, and Game categories when no category is specified, ensuring no single provider dominates search results.
- **Query Parameter Validation**: Implemented strict DRF serializers (`MediaSearchQuerySerializer`, `DiscoveryQuerySerializer`, `MediaListQuerySerializer`, `TrackingMediaQuerySerializer`, `DiaryLogFilterSerializer`, `ReviewMediaQuerySerializer`) to return controlled 400 Bad Request responses rather than 500 exceptions on invalid query inputs.
- **Security Hardening**: Made `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` environment-controlled in `settings.py`. Added comprehensive `.gitignore` ensuring `.env`, SQLite, and build files are excluded from git.
- **Project Dependency Definition**: Pinned core backend dependencies (`Django==5.2.7`, `djangorestframework==3.18.0`, `django-cors-headers==4.9.0`, `requests==2.32.3`) in `requirements.txt`.
- **Data Integrity Regression Test**: Added `DataIntegrityRegressionTestCase` proving provider synchronization can NEVER alter user-owned `UserMediaStatus`, `UserMediaProgress`, `SeriesProgress`, `MangaProgress`, `GameProgress`, `DiaryLog`, or `MediaReview`.
- **100% Offline Test Suite**: Fully isolated unit tests with deterministic `unittest.mock` fixtures. Expanded test suite to 56 automated tests passing in 37.9s without live network socket dependencies. Live reachability tests isolated in `python manage.py test_external_providers`.

---

## [0.4.0-alpha] - 2026-10-03

### Added
- **Corrected Reaction Visual Model**: Completely removed reaction icons and emojis from models, migrations, seed data, and documentation. Established pure typography text labels and approved color design tokens (Peak: Electric Gold, Loved It: Warm Coral, Good Time: Radiant Teal, Not My Thing: Muted Lavender, Skip: Crimson). Removed `icon` column from `ReactionDefinition`.
- **External Provider Architecture**: Created `ExternalProvider` and `ExternalMediaMapping` models with `UniqueConstraint(fields=['provider', 'external_id'])`.
- **Metadata Provider Adapters**: Built `BaseMetadataProvider` interface and adapters for TMDB (Movies, TV Series), AniList (Manga, Manhwa GraphQL), Jikan (Manga/Manhwa REST v4 fallback), and RAWG (Video Games).
- **Provider Registry & Fallback Layer**: Implemented `ProviderRegistry` providing category-based routing, automatic AniList -> Jikan fallback on failure/rate-limiting, and error-tolerant processing.
- **On-Demand Import & Deduplication**: Built `registry.import_media()` with 24-hour cache freshness check (`CATALOG_SYNC_FRESHNESS_HOURS`), deduplication by provider and external ID, and strict preservation of user-owned tracking and review data.
- **Core Catalog Endpoints**: Built `GET /api/v1/media/`, `GET /api/v1/media/<slug>/`, and `POST /api/v1/media/import/`.
- **Unified Candidate Search Endpoint**: Built `GET /api/v1/media/search/?q=&category=` returning normalized results tagged with `is_imported` and local slug.
- **Discovery Feeds**: Built `GET /api/v1/discovery/<category>/` for Movies, TV Series, Manga, Manhwa, and Video Games without database pollution.
- **Provider Attribution API**: Built `GET /api/v1/catalog/providers/` serving data-driven legal attribution notices for TMDB, AniList, Jikan, and RAWG.
- **Tracking & Diary REST Endpoints**: Implemented `POST`/`PATCH` endpoints for Status and Progress, and history-preserving Diary Log CRUD (`POST`, `GET`, `PATCH`, `DELETE`).
- **Universal Reactions & Review Endpoints**: Implemented `GET /api/v1/reviews/reactions/` (5 qualitative reactions with color tokens and no icons) and Review CRUD (`POST`, `GET`, `PATCH`, `DELETE`).
- **Session Auth & CSRF Endpoints**: Implemented `GET /api/v1/users/csrf/`, `POST /api/v1/users/login/`, `POST /api/v1/users/logout/`, and `GET`/`PATCH /api/v1/users/me/`.
- **Security & Templates**: Created `.env.example`; provider credentials loaded server-side only from environment; zero frontend API key leakage.
- **Automated Test Suite**: 46 automated unit and integration tests passing with 100% success rate, verifying provider normalization, fallback, deduplication, APIs, zero-star rating guarantee, and no-icon assertion.
- **Documentation**: Created `docs/PROVIDER_INTEGRATION.md` and updated all affected architecture/spec files.

---

## [0.3.0-alpha] - 2026-10-03
### Added
- **Django Project Foundation**: Initialized `dreamteal` project with SQLite, CORS, CSRF, and Session Authentication configured.
- **Modular Django Applications**: Created `apps/catalog`, `apps/tracking`, `apps/reviews`, and `apps/users`.
- **Media Catalog Models**: Built base `MediaItem` (UUID, slug, release year, poster/backdrop, genres, tags) and 1:1 detail extension models (`MovieDetail`, `SeriesDetail`, `MangaDetail`, `GameDetail`) with strict category validation.
- **User Profile Model**: Built `UserProfile` auto-created via `post_save` signal on standard Django `User`.
- **User Tracking & Progress Models**: Implemented `UserMediaStatus` with per-medium status validation and `UserMediaProgress` with category-specific extensions (`SeriesProgress`, `MangaProgress`, `GameProgress`).
- **History-Preserving DiaryLog**: Implemented `DiaryLog` with controlled editing, discrete row preservation for rewatches, and automatic forward progress synchronization with historical non-reversal safeguards.
- **Universal Reaction System**: Built `ReactionDefinition` dynamically storing DreamTeal's 5 approved qualitative verdicts (⚡ Peak, 💎 Loved It, 🍿 Good Time, 🌙 Not My Thing, 🛑 Skip) and `MediaReview` with strict uniqueness constraints and zero star rating attributes.
- **Admin Configuration**: Configured full Django Admin suite with stacked inlines, list filters, search fields, and list displays.
- **Seed Management Command**: Created `python manage.py seed_catalog` provisioning the 5 reaction definitions, standard development test user, genres, tags, and 4 multi-category sample catalog items.
- **Automated Test Suite**: Authored 27 automated backend tests across all apps, verifying constraints, cascades, automatic forward diary sync, non-reversal rules, and an automated schema audit proving zero star rating fields exist in the database. All 27 tests passing.

---

## [0.2.0-alpha] - 2026-10-03
### Added
- **Approved 5 Universal Reactions**: Finalized DreamTeal reaction taxonomy across Movies, TV Series, Manga, Manhwa/Webtoons, and Video Games: ⚡ Peak, 💎 Loved It, 🍿 Good Time, 🌙 Not My Thing, 🛑 Skip.
- **Approved Category Progress Architecture**: Finalized base `UserMediaProgress` with `SeriesProgress`, `MangaProgress`, and `GameProgress` extension models.
- **Approved Automatic Diary Synchronization**: Established automatic forward advancement of progress upon diary logging, with strict historical non-reversal safeguards and game playtime accumulation rules.
- **Approved Session Authentication**: Finalized Django Session Authentication with CSRF protection and local Vite development proxy.
- **Initiated Phase 1**: Transitioned project status to Phase 1 (Backend Data Foundations).

---

## [0.1.1-alpha] - 2026-10-03
### Changed
- **Reaction System**: Removed unconfirmed reaction badge names (`Masterpiece`, `Must Experience`, `Casual Fun`, `Pass`); marked reaction system as APPROVED and badge taxonomy/labels as PENDING USER DECISION. Designed dynamic `ReactionDefinition` data model.
- **Authentication**: Deleted DEC-007; eliminated hardcoded "Kartik" session assumption. Standardized on proper Django User / authentication architecture with seed/management commands for test accounts.
- **Diary Logging**: Replaced "Immutable" definition with "History-preserving diary records that users can edit through controlled log editing." Specified editable fields, discrete row preservation, rewatch representation, and deletion semantics.
- **Recommendations**: Marked deterministic recommendation architecture as APPROVED, scoring formula as PROVISIONAL, and numeric weights as NOT FINALIZED.
- **Progress Tracking**: Evaluated flat vs category-specific progress architectures; recommended Category-Specific Extension Models (`SeriesProgress`, `MangaProgress`, `GameProgress`) in `DATA_MODEL.md`.
- **API Contracts**: Disambiguated "Submit or update" endpoints into distinct RESTful `POST` (create) and `PATCH` (update) operations across all tracking and review resources.
- **Consistency**: Synchronized all 14 project documentation files across `docs/` and root `PROJECT_CONTEXT.md`.

---

## [0.1.0-alpha] - 2026-10-03
### Added
- Created Phase 0 Documentation Suite in `docs/` detailing requirements, decisions, architecture, data models, API contracts, design system, logging system, review system, recommendation system, media catalog, implementation roadmap, and progress tracker.
- Updated `PROJECT_CONTEXT.md` as master blueprint linking to all documentation files.

### Changed
- Revised product specifications to explicitly remove all star rating components, database fields, API fields, UI elements, and recommendation logic.
- Separated status, progress, diary log, and review entities into clean distinct database models.
