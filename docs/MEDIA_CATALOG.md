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
  - Decoupled via `ExternalProvider` and `ExternalMediaMapping` tables. All legacy direct provider ID fields (`tmdb_id`, `mal_id`, `rawg_id`) have been removed from `MediaItem`.
  - Providers: TMDB (Movies, TV Series), AniList (Manga, Manhwa), Jikan (Manga fallback), RAWG (Video Games).
  - External deduplication: `UniqueConstraint(fields=['provider', 'external_id'])` guarantees that a provider's external ID maps to exactly one DreamTeal `MediaItem`.
  - Multi-Provider Linking & Deduplication Service: `MediaMatcherService` calculates confidence scores ($\ge 75.0$ threshold) using media type, title/alt-titles, release years, and creators to link multiple providers (e.g. AniList and Jikan) to a single `MediaItem` without generating duplicate catalog entries.
  - Streaming Providers: Region-aware lookup via `DEFAULT_PROVIDER_REGION` (default `'IN'`) without arbitrary country fallbacks.
  - Discovery Modes: Semantics cleanly differentiate `popular`, `latest`, `trending`, and `upcoming` feeds per provider.
  - Caching & Freshness: Metadata is cached locally in DreamTeal models with `last_synced_at`. Items synced within 24 hours are served locally without hitting external APIs.
  - Zero-Star Rating Guarantee: Third-party ratings (TMDB vote_average, AniList averageScore, Jikan score, RAWG rating) are strictly excluded from DreamTeal.

---

## 4. Metadata Ownership & Taxonomy Reconciliation

### Metadata Ownership Boundaries
1. **Provider-Owned Metadata**: Third-party fields (title, synopsis, release year, poster/backdrop URLs, genre links, tag links, runtime, creators/directors, studios, platforms) are synchronized from upstream providers. When `force_refresh=True` is passed to the import service, these fields are updated with the latest provider data.
2. **Platform Catalog Metadata**: Slugs, canonical media types (`MOVIE`, `SERIES`, `MANGA`, `GAME`), and timestamps remain immutable.
3. **User-Owned Metadata**: Statuses, progress tracking, diary logs, qualitative reviews, and collections are strictly immutable to any catalog sync operations.

### Taxonomy Reconciliation
- Provider-supplied taxonomy is reconciled on sync: when metadata is refreshed, current provider genres and tags are assigned to the `MediaItem` via relation sets (`genres.set(...)`, `tags.set(...)`).
- Future manually curated tags will be isolated in dedicated curation models or tagged with curation origins so automatic sync never destroys user or editor annotations.

### Manga vs Manhwa Distinction
- DreamTeal maintains a single canonical media category: `MANGA`.
- Subtype discrimination (`MANGA`, `MANHWA`, `MANHUA`, `WEBTOON`) is stored in `MangaDetail.manga_type`.
- Discovery and search queries pass `subtype` filters (`countryOfOrigin: "KR"` for AniList, `type: 'manhwa'` for Jikan) so users querying Manhwa receive authentic Manhwa results rather than generic Manga.



