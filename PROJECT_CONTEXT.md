# DreamTeal Master Blueprint & Context Document

Welcome to **DreamTeal** — your custom unified pop-culture tracking, logging, reviewing, collection, discovery, and recommendation platform for **Movies**, **TV Series**, **Manga/Manhwa**, and **Video Games**.

---

## Source of Truth Documentation

All technical and product specifications are maintained in the [`docs/`](docs) folder. Below are direct links to each reference document:

1. 📋 [Product Requirements Document (PRD)](docs/PRODUCT_REQUIREMENTS.md)
2. 🏛️ [Architectural & Product Decisions](docs/PRODUCT_DECISIONS.md)
3. 🏗️ [System Architecture](docs/ARCHITECTURE.md)
4. 🗄️ [Data Model Specification](docs/DATA_MODEL.md)
5. 🔌 [API Contract Specification](docs/API_CONTRACT.md)
6. 🎨 [UI/UX Design System](docs/UI_DESIGN_SYSTEM.md)
7. 📅 [Logging & Progress System Architecture](docs/LOGGING_SYSTEM.md)
8. 💬 [Reaction-Based Review System Architecture](docs/REVIEW_SYSTEM.md)
9. 🧩 [Recommendation Engine Architecture](docs/RECOMMENDATION_SYSTEM.md)
10. 📚 [Media Catalog Architecture](docs/MEDIA_CATALOG.md)
11. 🌐 [External Provider Integration Specification](docs/PROVIDER_INTEGRATION.md)
12. 🚀 [Step-by-Step Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)
13. 📊 [Progress Tracker](docs/PROGRESS.md)
14. 📝 [Changelog](docs/CHANGELOG.md)


---

## Key Core Principles

### 1. Zero Star Ratings & Universal Qualitative Reaction System [APPROVED]
Star ratings, numeric scores (0.5–5, /10), and average rating numbers are **completely excluded** from the database, API, UI, sorting, and recommendation logic. DreamTeal uses ONE universal qualitative reaction system across all media (Movies, Series, Manga, Games) identified primarily through dedicated typography, text labels, and color design tokens (no emojis or generic icon sets):
- **Peak**: An exceptional experience that the user strongly recommends. (*Color: Electric Gold*)
- **Loved It**: A genuinely enjoyable experience that the user highly values. (*Color: Warm Coral*)
- **Good Time**: Enjoyable and worth experiencing, but not exceptional. (*Color: Radiant Teal*)
- **Not My Thing**: The user did not connect with it, even if the media may have strengths. (*Color: Muted Lavender*)
- **Skip**: The user would not recommend spending time on it. (*Color: Crimson*)

*Critical*: These are qualitative reactions, NOT hidden numeric ratings. They are never mapped to stars, never displayed as numbers, always display their clear text label, and do not use icons or emoji in the database or UI.

### 2. Strict Entity Separation [APPROVED]
The system strictly distinguishes:
- **Media Catalog Item** (Global catalog item: Movie, TV Series, Manga/Manhwa, Video Game)
- **User Media Status** (Current state: e.g., `Watching`, `Completed`, `Backlog`, `Dropped`)
- **User Media Progress** (Current position via category-specific extensions: `SeriesProgress`, `MangaProgress`, `GameProgress`)
- **Diary Log** (History-preserving diary records representing distinct consumption sessions: "I consumed this on this date.")
- **Media Review** (Qualitative reaction badge + written critique: "This is how I feel about this media.")

### 3. Automatic Diary → Progress Synchronization [APPROVED]
Logging a diary entry automatically advances current progress forward. Historical diary entries never move active progress backward.

### 4. Django Session Authentication & CSRF Architecture [APPROVED]
Uses Django Session Authentication with CSRF protection for secure communication with the React frontend, supporting both same-origin production and local Vite development proxy.

### 5. In-House Recommendation Engine
Answers *"What should I watch/read/play next?"* directly on the platform using a deterministic architecture (genres, vibes/tags, user history, and cross-category media relationships). Scoring formulas and weights are provisional.

### 6. Code Quality & Readability
All backend Django apps and React components include clear inline comments explaining what each module does, field definitions, business logic, and API data flow for developer readability.

### 7. Canonical Provider Identity & Metadata Ownership [APPROVED]
- All legacy direct provider ID fields (`tmdb_id`, `mal_id`, `rawg_id`) are completely removed from `MediaItem`. Third-party identity lives exclusively in `ExternalProvider` and `ExternalMediaMapping`.
- Clear metadata ownership boundary: Provider-owned catalog metadata (title, synopsis, release year, posters, backdrops, genres, tags, detail models) are refreshed on `force_refresh=True` with reconciled taxonomy. User-owned tracking, progress, diary logs, reviews, and collections are strictly immutable to external provider sync.
- Manga vs Manhwa: Single local type `MANGA` with `MangaDetail.manga_type` distinguishing `MANGA`, `MANHWA`, `MANHUA`, and `WEBTOON`. AniList and Jikan adapters pass subtype filters (`countryOfOrigin: KR` / `type=manhwa`) to retrieve authentic Manhwa.

### 8. Environment Security & Game Playtime Invariants [APPROVED]
- Real `.env` loading via `python-dotenv`. Hard-coded fallback secrets are banned; production startup without `SECRET_KEY` fails immediately with `ImproperlyConfigured`.
- Game diary sessions are the transactional source of truth for playtime. `GameProgress.hours_played` is maintained consistently across session creation, edit (delta calculation), deletion (deducting synced hours), and is unaffected when `sync_progress=False`.
- Private reviews (`is_public=False`) are visible only to their owner (`404 Not Found` for anonymous and non-owning authenticated users).

