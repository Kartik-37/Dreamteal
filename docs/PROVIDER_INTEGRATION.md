# DreamTeal External Metadata Provider Integration Specification

## 1. Overview & Architectural Principles

DreamTeal interfaces with third-party pop-culture metadata providers exclusively through a backend-only adapter layer. The React frontend **never** calls third-party APIs directly.

```text
React Frontend (Vite)
       │
       ▼ (Internal JSON REST API only)
DreamTeal Django REST API (/api/v1/media/search/, /api/v1/discovery/, /api/v1/media/import/)
       │
       ▼
Catalog Provider Service Layer (apps.catalog.providers)
  ├── BaseMetadataProvider (Common Interface & Capability Contracts)
  ├── ProviderRegistry (Routing, Balanced Interleaving & Fallback)
  ├── MediaMatcherService (Multi-Signal Cross-Provider Deduplication)
  ├── TMDBProvider (Movies & TV Series; Region-Aware Watch Providers)
  ├── AniListProvider (Manga & Manhwa GraphQL; idMal Linkage)
  ├── JikanProvider (Manga / Manhwa Fallback)
  └── RAWGProvider (Video Games)
       │
       ▼
External Provider APIs (TMDB, AniList, Jikan, RAWG)
```

---

## 2. Comprehensive Provider Capability Matrix

| Capability / Attribute | **TMDB** | **AniList** | **Jikan** (MAL Fallback) | **RAWG** |
| :--- | :--- | :--- | :--- | :--- |
| **Media Categories** | Movies, TV Series | Manga, Manhwa, Manhua | Manga, Manhwa, Light Novels | Video Games |
| **Protocol** | REST v3 | GraphQL v2 | REST v4 | REST v1 |
| **Authentication** | Bearer Token / API Key | None (Public GraphQL) | None (Public REST) | API Key (`key=...`) |
| **Search** | Native (`/search/movie`, `/search/tv`) | Native (`Page.media(search)`) | Native (`/manga?q=...`) | Native (`/games?search=...`) |
| **Details** | Full (`/movie/{id}`, `/tv/{id}`) | Full (`Media(id)`) | Full (`/manga/{id}/full`) | Full (`/games/{id}`) |
| **Popular Feed** | `/movie/popular`, `/tv/popular` | `sort: [POPULARITY_DESC]` | `/top/manga?filter=bypopularity` | `ordering=-added` |
| **Latest / New Releases** | `/movie/now_playing`, `/tv/on_the_air` | `sort: [START_DATE_DESC]` | `/manga?order_by=start_date` | `dates={180d_ago},{today}` |
| **Trending Feed** | `/trending/movie/week`, `/tv/week` | `sort: [TRENDING_DESC]` | *Fallback to Popular* | *Fallback to Popular* |
| **Upcoming Feed** | `/movie/upcoming`, `/tv/on_the_air` | `status: NOT_YET_RELEASED` | `/top/manga?filter=upcoming` | `dates={today},{+1yr}` |
| **Genres & Tags** | Genres mapped to global models | Genres mapped to global models | Genres mapped to global models | Genres & Tags mapped to models |
| **Images** | Poster (w500), Backdrop (w1280) | Cover (large), Banner | JPG Large, JPG Default | Background Image, Additional |
| **Watch / OTT Providers** | Region-aware (`/watch/providers`) | N/A | N/A | Store platforms / links |
| **External IDs** | TMDB Numeric ID | AniList ID + `idMal` | MyAnimeList ID | RAWG Slug / Numeric ID |
| **Rate Limitations** | ~40-50 req/sec | 90 req/min | 3 req/sec (strict) | 20,000 req/month |
| **Default Cache Freshness**| 24 Hours | 24 Hours | 24 Hours | 24 Hours |
| **Attribution Requirement**| Mandatory logo/text disclaimer | Mandatory API attribution | Mandatory open-source MAL notice | Mandatory RAWG.io link |
| **Fallback Role** | Primary for Movies/Series | Primary for Manga/Manhwa | Secondary fallback for AniList | Primary for Video Games |

---

## 3. Discovery Semantics

DreamTeal strictly distinguishes between four discovery feed concepts:

1. **Latest / New Releases (`latest`)**:
   - **Movies**: Currently in theatres / fresh VOD releases (`/movie/now_playing`).
   - **TV Series**: Currently on the air (`/tv/on_the_air`).
   - **Manga / Manhwa**: Ordered by publication start date (`START_DATE_DESC`).
   - **Video Games**: Released within the last 180 days (`ordering=-released`).
2. **Popular (`popular`)**:
   - Long-term or sustained engagement across user communities (TMDB popular, AniList popularity, RAWG `-added`).
3. **Trending (`trending`)**:
   - Rapid momentum or conversation spikes over the past 7 days (TMDB weekly trending, AniList `TRENDING_DESC`).
   - Where a provider does not provide native trending metrics (Jikan, RAWG), the adapter gracefully falls back to `popular` with transparent documentation rather than inventing fabricated scores.
4. **Upcoming (`upcoming`)**:
   - Officially scheduled future releases (TMDB upcoming movies, AniList `NOT_YET_RELEASED`, RAWG future date ranges).

All discovery endpoints accept `?mode=popular|latest|trending|upcoming&limit=20` and validate query parameters through `DiscoveryQuerySerializer`.

---

## 4. AniList $\rightarrow$ Jikan Fallback Strategy

AniList IDs and MyAnimeList/Jikan IDs are distinct identifier spaces. When AniList is unreachable, times out, or returns a 500 error, DreamTeal executes the following safe fallback protocol:

1. **Search Fallback**:
   - If AniList search returns zero items or fails, `ProviderRegistry` automatically queries `JikanProvider.search(query)`.
   - Results are tagged with `provider='jikan'` and the item's MAL ID.
2. **Detail Fallback Rules**:
   - If `fetch_details('anilist', external_id)` fails, the system **never** passes the AniList ID directly to Jikan.
   - If a candidate title hint is available (e.g. from a prior search candidate or catalog record), the service queries Jikan by title.
   - `MediaMatcherService` compares the Jikan candidate's normalized title, media type, and release year against the target work.
   - Only if confidence meets or exceeds `MIN_CONFIDENCE_THRESHOLD = 75.0` will the Jikan details be linked and ingested.
   - Otherwise, the service returns a controlled `None` ("fallback unavailable"), preventing accidental linking of unrelated works.
3. **Deterministic `idMal` Bridging**:
   - AniList's GraphQL schema exposes `idMal` alongside the native AniList ID.
   - When fetching AniList details, DreamTeal captures `id_mal` and proactively generates an `ExternalMediaMapping` for Jikan, allowing seamless cross-provider lookups without fuzzy matching.

---

## 5. Safe Cross-Provider Deduplication (`MediaMatcherService`)

To prevent duplicate catalog items when a work exists across multiple providers (e.g., AniList and Jikan for manga, or future multi-source ingestion for movies), DreamTeal uses `MediaMatcherService` before creating any new `MediaItem`:

```text
External Detail Ingested (e.g., Jikan MAL ID 121496)
                      │
                      ▼
Check Existing ExternalMediaMapping (provider='jikan', external_id='121496')
  ├── Found ──► Return existing MediaItem (200 OK)
  └── Not Found
        │
        ▼
MediaMatcherService.find_match(candidate)
  ├── Filter by exact media_type (MOVIE != MANGA != GAME)
  ├── Multi-signal scoring:
  │     ├── Direct ID link (AniList idMal == Jikan external_id): +100.0
  │     ├── Exact normalized title match: +40.0 (Alt title match: +35.0)
  │     ├── Release year exact match: +35.0 (Diff = 1: +15.0; Diff > 1: -50.0 PENALTY)
  │     └── Creator / Author / Director overlap: +30.0 (Studio / Publisher: +15.0)
  │
  ├── Score >= 75.0 ──► Confident Match! Merge mappings onto existing MediaItem (200 OK)
  └── Score < 75.0  ──► Create New MediaItem (201 Created)
```

### Guaranteed Outcomes:
- **Same work across two providers** (e.g. Solo Leveling on AniList and Jikan, same year 2018, same author Chugong) $\rightarrow$ Confidence $\ge 105.0 \rightarrow$ Merged into single `MediaItem`; both provider mappings are preserved.
- **Different works with same title** (e.g. *Solaris* 1972 vs *Solaris* 2002) $\rightarrow$ Year difference penalty (-50.0) drops confidence below 0.0 $\rightarrow$ Created as separate distinct `MediaItem` records.
- **Ambiguous candidates** (matching title but unknown years and missing creator data) $\rightarrow$ Confidence (40.0) remains below 75.0 threshold $\rightarrow$ Preserved as separate records to prevent erroneous data corruption.

---

## 6. Region-Aware TMDB Watch Providers

1. **Configurable Default Region**:
   - Read from Django configuration: `settings.DEFAULT_PROVIDER_REGION` (default `'IN'` for India, configurable via `.env`).
   - Never hardcoded into provider adapter logic.
2. **Regional Flatrate Filtering**:
   - `TMDBProvider` queries `data['watch/providers']['results'][self.default_region]`.
   - Extracts flatrate subscription services (e.g. JioCinema, Amazon Prime Video, Netflix, Disney+ Hotstar).
3. **No Arbitrary Region Fallback**:
   - If no watch data exists for the configured region, `ott_providers` defaults to an empty list `[]` (or networks fallback for broadcast TV).
   - DreamTeal never picks an arbitrary random country to populate missing regional data.
4. **Future User-Specific Personalization**:
   - The architecture is structured so user profile settings (`preferred_region`) can override `DEFAULT_PROVIDER_REGION` dynamically.

---

## 7. Media Import HTTP Status Lifecycle

The import endpoint `POST /api/v1/media/import/` accurately reflects creation lifecycle:
- **`201 Created`**: Returned when the work did not previously exist in DreamTeal and a new `MediaItem` catalog record was created.
- **`200 OK`**: Returned when the work already exists in DreamTeal (either through an existing provider mapping or via cross-provider deduplication) and was retrieved or refreshed.

---

## 8. Universal Multi-Media Search Distribution

When `GET /api/v1/media/search/?q=<query>` is called:
- **With Category (`?category=movie`)**: Directly routes to the category provider (TMDB) up to `limit`.
- **Without Category (Universal Search)**:
  - Allocates balanced quotas per category bucket: Movies, TV Series, Manga/Manhwa, Video Games.
  - Queries all 4 buckets simultaneously.
  - Interleaves results using round-robin distribution:
    `[Movie #1, Series #1, Manga #1, Game #1, Movie #2, Series #2, ...]`
  - Ensures video games and manga are never pushed out by prolific movie search results.

---

## 9. Data Integrity & User Data Immutability

Provider synchronization **strictly updates catalog-owned metadata only**. Provider sync is structurally barred from modifying:
- `UserMediaStatus`
- `UserMediaProgress`
- `SeriesProgress`
- `MangaProgress`
- `GameProgress`
- `DiaryLog`
- `MediaReview`
- `Collection` and `CollectionItem`

This invariant is verified by `DataIntegrityRegressionTestCase`.

---

## 10. Strict Zero-Star & Zero-Rating Policy

Third-party provider score and rating metrics:
- TMDB `vote_average` / `vote_count`
- AniList `averageScore` / `meanScore`
- Jikan / MyAnimeList `score` / `scored_by`
- RAWG `rating` / `metacritic`

are **completely excluded** from `NormalizedSearchResult`, `NormalizedMediaDetail`, database models, serializers, and API responses. DreamTeal exclusively uses its 5 qualitative reaction badges (Peak, Loved It, Good Time, Not My Thing, Skip).

---

## 11. Deterministic & Offline Testing Architecture

- **`python manage.py test`**:
  - 100% deterministic and offline.
  - All external HTTP calls to TMDB, AniList, Jikan, and RAWG are mocked via `unittest.mock.patch`.
  - Zero live network requests or external API dependencies.
- **`python manage.py test_external_providers`**:
  - Optional live connectivity verification command.
  - Tests reachability of active providers without blocking the main test suite.
