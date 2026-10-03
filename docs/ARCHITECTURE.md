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


