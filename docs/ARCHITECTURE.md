# DreamTeal System Architecture Document

## 1. System Overview

DreamTeal uses a decoupled architecture:
- **Backend**: Python 3.x, Django 5.x, Django REST Framework (DRF), and SQLite DB (architected for PostgreSQL readiness).
- **Frontend**: React (Vite), Tailwind CSS, Lucide Icons, and React Router.
- **Communication Protocol**: JSON REST API with clear response envelopes and error handling.

---

## 2. Backend System Architecture

```text
                               +-----------------------------+
                               |     React + Vite Frontend    |
                               +--------------+--------------+
                                              |
                                     JSON REST API (HTTP)
                                              |
                                              v
+-----------------------------------------------------------------------------------+
| Django REST Framework API Layer                                                   |
|  +---------------------+  +---------------------+  +---------------------------+  |
|  | Catalog API         |  | Tracking API        |  | Recommendation API        |  |
|  | /api/catalog/       |  | /api/logs/, /reviews|  | /api/recommendations/     |  |
|  +----------+----------+  +----------+----------+  +-------------+-------------+  |
+-------------|------------------------|---------------------------|----------------+
              |                        |                           |
              v                        v                           v
+-----------------------------------------------------------------------------------+
| Django Service Layer                                                              |
|  +---------------------+  +---------------------+  +---------------------------+  |
|  | CatalogService      |  | TrackingService     |  | RecommendationEngine      |  |
|  +----------+----------+  +----------+----------+  +-------------+-------------+  |
+-------------|------------------------|---------------------------|----------------+
              |                        |                           |
              v                        v                           v
+-----------------------------------------------------------------------------------+
| Django ORM Data Access Layer                                                      |
|  [MediaItem] <---- (MovieDetail / SeriesDetail / MangaDetail / GameDetail)        |
|  [UserMediaStatus]  [Progress Models]  [DiaryLog]  [MediaReview / ReactionDef]    |
+-----------------------------------------------------------------------------------+
```

---

## 3. Django Application Structure

- `apps/catalog/`: Handles `MediaItem` definitions, media-type specific extension models (`MovieDetail`, `SeriesDetail`, `MangaDetail`, `GameDetail`), genres, tags, streaming providers, and platform catalogs.
- `apps/tracking/`: Handles user status (`UserMediaStatus`), category-specific progress tracking (`UserMediaProgress` $\rightarrow$ `SeriesProgress`, `MangaProgress`, `GameProgress`), and history-preserving diary logs (`DiaryLog`) with automatic forward synchronization.
- `apps/reviews/`: Handles dynamic reaction definitions (`ReactionDefinition` seeded with 5 universal verdicts: ⚡ Peak, 💎 Loved It, 🍿 Good Time, 🌙 Not My Thing, 🛑 Skip), user reviews (`MediaReview`), spoiler masks, and review likes.
- `apps/collections/`: Handles user lists (`MediaCollection`) and collection items (`CollectionItem`).
- `apps/recommendations/`: Computes deterministic recommendation scores and cross-category matches ("What to watch/read/play next") using provisional scoring formulas and configurable weights.
- `apps/users/`: Handles standard Django User authentication (`django.contrib.auth.models.User`), relational user profiles (`UserProfile`), preferences, and session-based auth APIs.

---

## 4. Database Engine & Production Readiness

- **Current Database**: Built-in SQLite database for development and offline running.
- **PostgreSQL Readiness**: Models strictly use standard Django field types, indexing, and foreign key relations to allow seamless migration to PostgreSQL using `DATABASE_URL` settings.

---

## 5. Frontend-Backend Authentication & Session Architecture [APPROVED]

### 5.1 Protocol: Django Session Authentication + CSRF
- **Authentication**: Native Django Session Authentication using HTTP-only `sessionid` cookies. No JWT tokens.
- **CSRF Defense**: Django's standard CSRF middleware enforcing `csrftoken` cookie verification on all state-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`).
- **Endpoint**: `GET /api/v1/users/csrf/` provides an initial CSRF token; `POST /api/v1/users/login/` establishes authenticated sessions; `POST /api/v1/users/logout/` invalidates sessions.

### 5.2 Development vs Production Environment Setup
- **Local Vite Development**:
  - Vite dev server (`http://localhost:5173`) proxies all `/api/` traffic directly to Django (`http://127.0.0.1:8000`).
  - Browser treats requests as same-origin, automatically managing `sessionid` and `csrftoken` cookies without cross-origin cookie restrictions.
  - `django-cors-headers` configured with `CORS_ALLOW_CREDENTIALS = True` and local origin whitelisting.
- **Production Deployment**:
  - React production build served directly via Django or behind a unified reverse proxy (e.g. Nginx/Caddy) under the same domain, ensuring zero CORS complexity and strict HTTPS cookie security (`SESSION_COOKIE_SECURE = True`, `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`).

---

## 6. External Metadata Provider Architecture [APPROVED]

```text
React Frontend (Vite)
       │
       ▼ (Internal REST API only — React NEVER contacts third-party APIs)
DreamTeal Django REST API (/api/v1/media/search/, /api/v1/discovery/, /api/v1/media/import/)
       │
       ▼
Catalog Provider / Service Layer (apps.catalog.providers)
  ├── BaseMetadataProvider (Common Interface: search, get_details, discover, health_check)
  ├── ProviderRegistry (Routes categories, manages fallbacks & balanced universal search)
  ├── MediaMatcherService (Multi-signal cross-provider deduplication)
  ├── TMDBProvider (Movies & TV Series; Region-aware watch providers)
  ├── AniListProvider (Manga & Manhwa via AniList GraphQL; idMal bridging)
  ├── JikanProvider (Manga/Manhwa secondary fallback via Jikan v4 REST)
  └── RAWGProvider (Video Games via RAWG API)
       │
       ▼
External Third-Party APIs (TMDB, AniList, Jikan, RAWG)
```

### Architectural Guarantees:
1. **Frontend Isolation**: React frontend never communicates directly with external metadata providers. All external calls occur server-side.
2. **Provider Key Secrecy**: External credentials (`TMDB_ACCESS_TOKEN`, `RAWG_API_KEY`) reside exclusively in server environment variables.
3. **Data Isolation**: External metadata updates and imports NEVER alter user tracking, progress, diary logs, or reviews.
4. **Zero-Star Rating Guarantee**: External numeric rating scores (e.g., TMDB `vote_average`, AniList `averageScore`, RAWG rating) are never ingested, converted, or displayed as DreamTeal ratings.
5. **Cross-Provider Deduplication**: `(provider, external_id)` uniqueness and `MediaMatcherService` confidence scoring prevent duplicate records across providers.
6. **Fault Tolerance**: Network failures or rate limits from external APIs fail gracefully without bringing down the core application.
7. **Deterministic Offline Tests**: Main test suite executes 100% offline using deterministic mocks, keeping live API checks completely optional.
8. **Canonical Provider Identity**: All legacy direct provider ID fields (`tmdb_id`, `mal_id`, `rawg_id`) are completely removed from `MediaItem`; third-party identities are managed exclusively through `ExternalProvider` and `ExternalMediaMapping`.
9. **Safe Environment & Secret Security**: `.env` configuration is loaded automatically via `python-dotenv`. Hard-coded fallback secrets are barred from source code; missing production `SECRET_KEY` fails immediately at startup with `ImproperlyConfigured`.
10. **Provider Active State Routing**: Provider routing respects the `ExternalProvider.active` database switch, bypassing disabled providers in search, feeds, and imports.
11. **Transaction-Safe Diary Aggregation**: Game diary consumption sessions act as the transactional source of truth for session gameplay, with atomic updates/deletions maintaining consistent cumulative `GameProgress.hours_played`.

---

## 7. Recommendation Engine Architecture [APPROVED]

```text
React Frontend (Vite)
       │
       ▼
DRF API Layer: GET /api/v1/recommendations/next/<slug>/?cross_category=true&category=GAME&limit=10
       │
       ▼
apps.recommendations.views.RecommendationNextView
       │
       ▼
apps.recommendations.services.RecommendationEngine
  ├── 1. Candidate Retrieval (Single bulk prefetch query, category/cross-category filter)
  ├── 2. User History & Privacy Filtering (Excludes completed/consumed/dropped/paused/skip items)
  ├── 3. Tag & Vibe Jaccard Similarity (Weight: 40.0)
  ├── 4. Genre Jaccard Similarity (Weight: 30.0)
  ├── 5. Cross-Media & Franchise Adapter Detection (Weight: 15.0)
  ├── 6. User Reaction Affinity Scoring (Weight: 15.0 for Peak, Loved It, Good Time; penalty for Not My Thing)
  ├── 7. Threshold Filtering (min_evidence_score = 15.0)
  ├── 8. Human-Readable Match Explanation Generation
  └── 9. Deterministic Tie-Breaking & Bounded Slicing (limit: 1 to 50)
       │
       ▼
Serialized Response Envelope: Base Media + Recommended Items (UUID, slug, title, poster, reasons)
```

### Architectural Guarantees:
1. **100% Offline & Deterministic**: Zero reliance on machine learning, vector embeddings, external recommendation APIs, or randomized sampling. The engine runs entirely on local database metadata.
2. **Zero Star Ratings Guarantee**: Reactions (`Peak`, `Loved It`, `Good Time`, `Not My Thing`, `Skip`) are purely qualitative affinity signals and are never converted into star ratings or numeric averages.
3. **Privacy & Owner Scoping**: Personalized history and preference signals use only the requesting authenticated user's own data (`is_favorite`, positive reactions, diary logs). Private reviews and diary logs belonging to other users are strictly excluded. Anonymous users receive unbiased, general content-based similarity.
4. **No N+1 Queries**: Candidates are retrieved in a single bulk query with `select_related('movie_detail', 'series_detail', 'manga_detail', 'game_detail')` and `prefetch_related('genres', 'tags')`.
5. **Evidence Threshold**: Weak coincidental overlaps (such as sharing a single broad genre) fall below `min_evidence_score=15.0` and are pruned to prevent noisy suggestions.
6. **Explainable Match Reasons**: Every returned item includes transparent, human-readable match explanations supported strictly by actual catalog overlaps.
7. **Deterministic Tie-Breaking**: Ranks are sorted by `(-total_score, -shared_tags_count, -shared_genres_count, -release_year, title.lower(), str(id))`, ensuring identical output for identical database states.
