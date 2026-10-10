# DreamTeal

**DreamTeal** is a custom unified pop-culture tracking, logging, reviewing, collection, discovery, and recommendation platform across four major media categories:
- **Movies**
- **TV Series**
- **Manga & Manhwa / Webtoons**
- **Video Games**

DreamTeal eliminates the limitations of fragmented single-medium apps by consolidating multi-media tracking into a unified experience with an uncompromising visual identity.

---

## 🌟 Key Product Pillars

1. **Zero Star Ratings & Universal Qualitative Reactions**:
   - Star ratings, 0.5–5 scores, ratings out of 10, and numeric score averages are **completely excluded** from the platform.
   - DreamTeal uses one universal qualitative reaction system across all categories:
     - **Peak** (*Electric Gold*): An exceptional experience that the user strongly recommends.
     - **Loved It** (*Warm Coral*): A genuinely enjoyable experience that the user highly values.
     - **Good Time** (*Radiant Teal*): Enjoyable and worth experiencing, but not exceptional.
     - **Not My Thing** (*Muted Lavender*): The user did not connect with it, even if the media has strengths.
     - **Skip** (*Crimson*): The user would not recommend spending time on it.
   - Badges rely strictly on clear text labels, typography, and dedicated color tokens. No emojis or icon fields exist in the database or UI.
2. **Strict Entity Separation**:
   - Clean structural separation between:
     - **Media Catalog Item** (Global work metadata)
     - **User Media Status** (Current state: e.g., `Watching`, `Completed`, `Backlog`, `Dropped`)
     - **User Media Progress** (Current position via category-specific extensions: `SeriesProgress`, `MangaProgress`, `GameProgress`)
     - **Diary Log** (History-preserving timeline entries representing distinct consumption sessions)
     - **Media Review** (Qualitative reaction badge + written critique with public/private privacy controls)
3. **Automatic Forward Progress Synchronization & Transactional Game Tracking**:
   - Creating a diary entry automatically advances current progress forward. Historical diary entries never move active progress backward for series or manga.
   - Video game play sessions are aggregated into `GameProgress.hours_played` through an atomic service (`GameSessionTrackingService`), safely supporting session creation, edits, deletion, and bulk deletions without stale totals.
4. **Backend-Only Provider Adapter Architecture**:
   - The frontend never connects directly to third-party APIs. All communications are orchestrated through server-side adapters with strict credential isolation:
     - **TMDB**: Movies & TV Series (with region-aware watch providers)
     - **AniList**: Manga & Manhwa (GraphQL with `idMal` cross-referencing and format isolation)
     - **Jikan**: Manga fallback (unofficial MyAnimeList REST v4)
     - **RAWG**: Video Games (platforms, developers, publishers, playtime)
   - Multi-signal cross-provider deduplication (`MediaMatcherService`, confidence threshold $\ge 75.0$) ensures works across providers link to a single catalog record while preserving uncertainty when metadata is ambiguous.

---

## 🚀 Implemented vs Planned Features

### ✅ Implemented Features (Phase 0, Phase 1, Phase 2 & Phase 3 Complete)
- **Universal Catalog Data Model**: Base `MediaItem` with category-specific extension models (`MovieDetail`, `SeriesDetail`, `MangaDetail`, `GameDetail`), `Genre`, and `Tag`.
- **Qualitative Reaction System**: Universal 5-badge taxonomy with zero-star guarantees enforced at database, serializer, and view layers.
- **User Tracking State**: `UserMediaStatus` with strict lifecycle validation per media type.
- **Progress Validation**: `UserMediaProgress` rejecting incompatible nested progress types, enforcing non-negative ranges, and preventing unauthorized progress manipulation.
- **Diary Logging & Service-Based Playtime Aggregation**: `DiaryLog` supporting session snapshots, forward-only sync for series/manga, and atomic recalculation of game playtime via `GameSessionTrackingService`.
- **Review Privacy Controls**: Strict owner vs public access controls on individual reviews and review lists.
- **External Metadata Adapters**: TMDB, AniList, Jikan, and RAWG adapters with isolated mock testing.
- **Multi-Mode Discovery & Balanced Search**: Popular, latest, trending, and upcoming discovery feeds, alongside balanced multi-category round-robin search.
- **Session Authentication & CSRF Protection**: Django session authentication with CSRF enforcement on unsafe requests.
- **Deterministic Recommendation Engine**: In-house rule-based "What to watch/read/play next" recommendation engine (`GET /api/v1/recommendations/next/<slug>/`) with tag/genre Jaccard similarity, franchise adapter detection, user reaction affinity, strict evidence thresholds, transparent match explanations, and owner-scoped privacy boundaries.
- **Automated Verification**: Comprehensive offline test suite (132/132 passing tests).

### ⏳ Planned Features (Upcoming Milestones)
- **Phase 4 (Frontend Foundation & Component Library)**: Modern React + Vite web client with dark mode aesthetics, glassmorphism, micro-animations, and custom design tokens (no TailwindCSS).

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12+, Django 5.2.7, Django REST Framework 3.18.0
- **HTTP / CORS**: `requests 2.32.3`, `django-cors-headers 4.9.0`
- **Authentication**: Django Session Authentication with CSRF protection
- **Database**: SQLite in development (structured for straightforward PostgreSQL migration)
- **Frontend** *(Upcoming Phase 4)*: React with Vite, Vanilla CSS design tokens (no TailwindCSS)

---

## 💻 Local Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Kartik-37/Dreamteal.git
cd Dreamteal
```

### 2. Create and Activate Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```
Open `.env` and configure settings for your local development environment:
- `DEBUG`: Set to `True` for local development.
- `SECRET_KEY`: Use a unique development secret key locally. Never use production secrets or commit `.env`.
- `ALLOWED_HOSTS`: Default `127.0.0.1,localhost,testserver`.
- `DEFAULT_PROVIDER_REGION`: Default streaming provider region code (e.g. `IN`, `US`, `GB`).
- `TMDB_ACCESS_TOKEN` / `TMDB_API_KEY`: *(Optional)* For live TMDB queries.
- `RAWG_API_KEY`: *(Optional)* For live RAWG queries.
*(AniList GraphQL and Jikan REST function without API keys).*

### 5. Apply Migrations & Seed Development Data
```bash
python manage.py migrate
python manage.py seed_catalog
```
*The seed command provisions default reaction definitions, standard development user (`dreamteal_tester` / `dreamteal_pass123`), genres, tags, provider records, and sample catalog items.*

### 6. Run the Development Server
```bash
python manage.py runserver
```
The Django REST API will be available at `http://127.0.0.1:8000/`.

---

## 🧪 Testing

DreamTeal enforces a strict distinction between offline unit testing and live network checks:

### 1. Deterministic Offline Test Suite (Primary)
```bash
python manage.py test
```
- **100% Offline**: All external provider communications (TMDB, AniList, Jikan, RAWG) are mocked using deterministic `unittest.mock` fixtures.
- Covers data models, category-specific extensions, auto-sync, non-reversal rules, deduplication, search interleaving, query validation, CSRF enforcement, and zero-star audits.
- Current Status: **132/132 tests passing cleanly in ~146s**.

### 2. Optional Live Provider Connectivity Check
```bash
python manage.py test_external_providers
```
- Verifies live reachability and schema compatibility against public AniList GraphQL, Jikan REST, and configured TMDB/RAWG endpoints.

---

## 🌿 Git & GitHub Development Workflow

DreamTeal enforces structured version control rules documented in [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md):

- **Branch Model**:
  - `main`: Protected stable milestones only. Never commit active feature work directly to `main`.
  - `develop`: Integration branch for active, verified development.
  - `feature/*`: Specific feature branches (e.g. `feature/recommendation-engine`).
  - `fix/*`: Specific bug fixes.
- **Conventional Commits**: `feat(...)`, `fix(...)`, `test(...)`, `docs(...)`, `chore(...)`.
- **Phase Completion Gate**: A phase is only considered complete when implementation, tests, documentation, Git commit, GitHub push, and verification checks are 100% satisfied.

---

## 📚 Project Documentation Index

All technical specifications live in the [`docs/`](docs) folder:
- [Git & GitHub Workflow](docs/GIT_WORKFLOW.md)
- [Product Requirements Document (PRD)](docs/PRODUCT_REQUIREMENTS.md)
- [Architectural & Product Decisions](docs/PRODUCT_DECISIONS.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [External Provider Integration Specification](docs/PROVIDER_INTEGRATION.md)
- [Data Model Specification](docs/DATA_MODEL.md)
- [API Contract Specification](docs/API_CONTRACT.md)
- [UI/UX Design System](docs/UI_DESIGN_SYSTEM.md)
- [Reaction-Based Review System](docs/REVIEW_SYSTEM.md)
- [Logging & Progress System](docs/LOGGING_SYSTEM.md)
- [Recommendation Engine Architecture](docs/RECOMMENDATION_SYSTEM.md)
- [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)
- [Progress Tracker](docs/PROGRESS.md)
- [Changelog](docs/CHANGELOG.md)
