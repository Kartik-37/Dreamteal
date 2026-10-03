# DreamTeal Media Catalog Architecture

## 1. Overview
The Media Catalog is the foundational data registry of DreamTeal. It unifies Movies, TV Series, Manga/Manhwa, and Video Games into a structured database while preserving category-specific attributes.

---

## 2. Entity Hierarchy

```text
                        +----------------------+
                        |      MediaItem       |
                        | (Common Metadata)    |
                        +----------+-----------+
                                   |
         +-----------------+-------+-------+-----------------+
         |                 |               |                 |
         v                 v               v                 v
+----------------+ +---------------+ +---------------+ +---------------+
|  MovieDetail   | | SeriesDetail  | |  MangaDetail  | |  GameDetail   |
|  (Director,    | | (Seasons,     | | (Author,      | | (Developer,   |
|   Runtime,     | |  Episodes,    | |  Chapters,    | |  Platforms,   |
|   OTT links)   | |  Network)     | |  Format)      | |  Playtime)    |
+----------------+ +---------------+ +---------------+ +---------------+
```

---

## 3. Data Integrity & Deduplication Rules
- **Unique Slugs**: Formatted as `{title-kebab-case}-{release-year}` (e.g. `the-batman-2022`, `cyberpunk-2077-2020`).
- **Genres & Tags**: Standardized global lookups to prevent duplicate genre entries (e.g. "Sci-Fi" vs "Science Fiction").
- **Third-Party API Integration & External Mapping [APPROVED]**:
  - Decoupled via `ExternalProvider` and `ExternalMediaMapping` tables.
  - Providers: TMDB (Movies, TV Series), AniList (Manga, Manhwa), Jikan (Manga fallback), RAWG (Video Games).
  - External deduplication: `UniqueConstraint(fields=['provider', 'external_id'])` guarantees that a provider's external ID maps to exactly one DreamTeal `MediaItem`.
  - Multi-Provider Linking & Deduplication Service: `MediaMatcherService` calculates confidence scores ($\ge 75.0$ threshold) using media type, title/alt-titles, release years, and creators to link multiple providers (e.g. AniList and Jikan) to a single `MediaItem` without generating duplicate catalog entries.
  - Streaming Providers: Region-aware lookup via `DEFAULT_PROVIDER_REGION` (default `'IN'`) without arbitrary country fallbacks.
  - Discovery Modes: Semantics cleanly differentiate `popular`, `latest`, `trending`, and `upcoming` feeds per provider.
  - Caching & Freshness: Metadata is cached locally in DreamTeal models with `last_synced_at`. Items synced within 24 hours are served locally without hitting external APIs.
  - Zero-Star Rating Guarantee: Third-party ratings (TMDB vote_average, AniList averageScore, Jikan score, RAWG rating) are strictly excluded from DreamTeal.


