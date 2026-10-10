# DreamTeal Step-by-Step Implementation Roadmap

Development for DreamTeal strictly follows a phased, verified approach. No phase will begin until the previous phase is fully completed and verified.

---

## Roadmap Phases

### Phase 0: Requirements Discovery & Clarification (COMPLETED)
- [x] Inspect reference screenshots (Moctale & Letterboxd).
- [x] Identify core UX patterns and eliminate contradictions (completely remove star ratings, separate log vs status vs review).
- [x] Author comprehensive documentation suite (`docs/*`).
- [x] Align documentation with user feedback (provisional recommendation weights, dynamic reaction definitions, history-preserving editable diary, category-specific progress evaluation, standard Django auth).
- [x] Finalize remaining product decisions with user:
  - Approved 5 universal reaction definitions (⚡ Peak, 💎 Loved It, 🍿 Good Time, 🌙 Not My Thing, 🛑 Skip)
  - Approved category-specific progress architecture (`SeriesProgress`, `MangaProgress`, `GameProgress`)
  - Approved automatic Diary $\rightarrow$ Progress synchronization with historical non-reversal rules
  - Approved Django Session Authentication + CSRF architecture

---

### Phase 1: Architecture & Data Foundations (COMPLETED & VERIFIED)
Implement backend data foundations in strict verified order:
- [x] 1. Django project foundation (`dreamteal` configuration, settings with SQLite and CORS/CSRF)
- [x] 2. Django modular applications (`catalog`, `tracking`, `reviews`, `users`)
- [x] 3. Base catalog model (`MediaItem`)
- [x] 4. Genre / tag relational models (`Genre`, `Tag`)
- [x] 5. Movie detail model (`MovieDetail`)
- [x] 6. Series detail model (`SeriesDetail`)
- [x] 7. Manga / Manhwa detail model (`MangaDetail`)
- [x] 8. Game detail model (`GameDetail`)
- [x] 9. User profile model (`UserProfile` linked to `django.contrib.auth.models.User`)
- [x] 10. User media status model (`UserMediaStatus`)
- [x] 11. User media progress base model (`UserMediaProgress`)
- [x] 12. Series progress model (`SeriesProgress`)
- [x] 13. Manga progress model (`MangaProgress`)
- [x] 14. Game progress model (`GameProgress`)
- [x] 15. History-preserving diary log model (`DiaryLog`) with forward-sync logic
- [x] 16. Reaction definition model (`ReactionDefinition` - strictly non-numeric, typography and color tokens, no icons)
- [x] 17. Media review model (`MediaReview`)
- [x] 18. Database constraints and indexes (uniqueness, cascade, validation)
- [x] 19. Django database migrations
- [x] 20. Django admin configuration for all models
- [x] 21. Development seed/management command (`seed_catalog`) provisioning reaction definitions, test user, sample catalog, and provider records
- [x] 22. Backend test suite verifying data integrity, constraints, no star-rating columns, and seed accuracy

---

### Phase 2: Core Backend REST API + External Media Providers (COMPLETED & VERIFIED)
- [x] Visual Model Correction: Completely eliminated reaction icons/emoji; implemented dedicated color tokens and typography text labels; removed `icon` column from database.
- [x] External Provider Architecture: Extensible `BaseMetadataProvider` interface and adapters for TMDB, AniList, Jikan, and RAWG.
- [x] Discovery Semantics Correction: Distinct `popular`, `latest`, `trending`, and `upcoming` feeds across all providers.
- [x] Canonical Provider Identity: Removed legacy `tmdb_id`, `mal_id`, `rawg_id` from `MediaItem`; third-party identity stored exclusively in `ExternalProvider` and `ExternalMediaMapping` with migration `0003`.
- [x] Real Environment Loading: Integrated `python-dotenv` to load `.env` automatically; removed hard-coded `SECRET_KEY` fallbacks; enforced startup validation in production (`ImproperlyConfigured`).
- [x] True Manga vs Manhwa Search & Discovery: Filtered AniList by `countryOfOrigin` (`KR` vs `JP`) and Jikan by `type` (`manhwa` vs `manga`) without altering the canonical `MediaItem.media_type = MANGA`.
- [x] Real Metadata Refresh & Taxonomy Reconciliation: Enabled updating of provider-owned catalog metadata on `force_refresh=True` and reconciled provider taxonomy (`genres`, `tags`) while strictly protecting user-owned data.
- [x] Verified Seed Data Provider IDs: Verified all seed provider mappings (Cyberpunk 2077 -> RAWG 41494 `cyberpunk-2077`) with automated validation preventing invalid bindings.
- [x] AniList $\rightarrow$ Jikan Import Fallback: Integrated `title_hint` into `import_media` and `fetch_details` with `MediaMatcherService` confidence scoring ($\ge 75.0$).
- [x] Transaction-Safe Game Diary Aggregation: Consumption sessions are the source of truth for playtime; edits and deletions atomically update `GameProgress.hours_played` without double-counting via `GameSessionTrackingService`; isolated when `sync_progress=False`.
- [x] Privacy & Access Control Enforcement: Scoped private reviews strictly to owners (`404 Not Found` for non-owners); scoped all tracking querysets to authenticated users.
- [x] Provider Active State Routing: Respects `ExternalProvider.active` database switch across search, discovery, and imports.
- [x] Region-Aware TMDB Watch Providers: Configurable `DEFAULT_PROVIDER_REGION=IN` without arbitrary country fallbacks.
- [x] Media Import Lifecycle: Returns `201 Created` for new records, `200 OK` for existing/refreshed records.
- [x] Balanced Universal Search: Category-aware quotas and round-robin interleaving preventing provider domination.
- [x] Contract & Progress Validation: Nested progress validation rejecting incompatible categories, numeric bounds checks, `media_id` vs `media_item` bidirectional compatibility.
- [x] 100% Offline Test Suite: 88 automated unit and integration tests passing offline with deterministic mocks.



---

### Phase 3: Recommendation Engine Implementation
- [ ] Build similarity scoring algorithm service (`RecommendationEngine`).
- [ ] Implement `GET /api/v1/recommendations/next/<slug>/` endpoint.
- [ ] Test cross-media recommendation logic (e.g. matching Anime/Manga to Video Games).

---

### Phase 4: Frontend Foundation & Component Library
- [ ] Set up React (Vite) + Tailwind CSS app structure.
- [ ] Create UI Design System primitives (Color palette, dark background, poster cards, badge components, navigation bar).
- [ ] Integrate API service layer (`src/services/api.js`).

---

### Phase 5: Core Pages & Interactive UX
- [ ] Build Home & Explore / Discovery Hub with category tabs & vibe filters.
- [ ] Build Media Detail Page with hero backdrop, metadata, reaction reviews, and "What to consume next" recommendation carousel.
- [ ] Build Modal Logging Interface for quick status updates, chapter tracking, hours played, and diary logs.
- [ ] Build Letterboxd-style Diary / History view grouped by month/date.
- [ ] Build User Profile & Collections pages.

---

### Phase 6: End-to-End Verification & Polish
- [ ] Run backend unit tests and API checks.
- [ ] Verify full responsive UI/UX flow on desktop and mobile viewports.
- [ ] Audit code readability, inline comments, and developer documentation.
