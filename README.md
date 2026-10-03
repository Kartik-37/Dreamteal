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
     - **Media Review** (Qualitative reaction badge + written critique)
3. **Automatic Forward Progress Synchronization**:
   - Creating a diary entry automatically advances current progress forward. Historical diary entries never move active progress backward.
4. **Backend-Only Provider Adapter Architecture**:
   - The frontend never connects directly to third-party APIs. All communications are orchestrated through server-side adapters with strict credential isolation:
     - **TMDB**: Movies & TV Series (with region-aware watch providers)
     - **AniList**: Manga & Manhwa (GraphQL with `idMal` cross-referencing)
     - **Jikan**: Manga fallback (unofficial MyAnimeList REST v4)
     - **RAWG**: Video Games (platforms, developers, publishers, playtime)
   - Multi-signal cross-provider deduplication (`MediaMatcherService`) ensures works across providers (e.g. AniList and Jikan) link to a single catalog record.

---

## 🚀 Current Project Stage

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 0** | Product Discovery & Specifications | **COMPLETED & APPROVED** |
| **Phase 1** | Backend Data Foundations & Models | **COMPLETED & VERIFIED** |
| **Phase 2** | Core REST API & External Metadata Providers | **COMPLETED & VERIFIED** (56/56 Tests Passing) |
| **Phase 3** | In-House Deterministic Recommendation Engine | *Pending Next Milestone* |
| **Phase 4** | React + Vite Modern Frontend | *Deferred until Phase 3 completion* |

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
git clone <repository-url>
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
Open `.env` and configure settings as desired:
- `DEBUG`: `True` in local development.
- `SECRET_KEY`: Keep default dev key locally; set custom secret in production.
- `DEFAULT_PROVIDER_REGION`: Default streaming provider region code (e.g. `IN`, `US`, `GB`).
- `TMDB_ACCESS_TOKEN` / `TMDB_API_KEY`: *(Optional)* for live TMDB queries.
- `RAWG_API_KEY`: *(Optional)* for live RAWG queries.
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
- Covers data models, category-specific extensions, auto-sync, non-reversal rules, deduplication, search interleaving, query validation, and zero-star audits.
- Current Status: **56/56 tests passing cleanly in ~37s**.

### 2. Optional Live Provider Connectivity Check
```bash
python manage.py test_external_providers
```
- Verifies live reachability and schema compatibility against public AniList GraphQL, Jikan REST, and configured TMDB/RAWG endpoints.

---

## 🌿 Git & GitHub Development Workflow

DreamTeal enforces structured version control rules documented in [`docs/GIT_WORKFLOW.md`](file:///c:/Users/OM/Desktop/Dreamteal/docs/GIT_WORKFLOW.md):

- **Branch Model**:
  - `main`: Protected stable milestones only. Never commit active feature work directly to `main`.
  - `develop`: Integration branch for active, verified development.
  - `feature/*`: Specific feature branches (e.g. `feature/recommendation-engine`).
  - `fix/*`: Specific bug fixes.
- **Conventional Commits**: `feat(...)`, `fix(...)`, `test(...)`, `docs(...)`, `chore(...)`.
- **Phase Completion Gate**: A phase is only considered complete when implementation, tests, documentation, Git commit, GitHub push, and verification checks are 100% satisfied.
- **Milestone Tags**: Stable releases are tagged (e.g., `v0.4.1-alpha`).

---

## 📚 Project Documentation Index

All technical specifications live in the [`docs/`](file:///c:/Users/OM/Desktop/Dreamteal/docs) folder:
- [Git & GitHub Workflow](file:///c:/Users/OM/Desktop/Dreamteal/docs/GIT_WORKFLOW.md)
- [Product Requirements Document (PRD)](file:///c:/Users/OM/Desktop/Dreamteal/docs/PRODUCT_REQUIREMENTS.md)
- [Architectural & Product Decisions](file:///c:/Users/OM/Desktop/Dreamteal/docs/PRODUCT_DECISIONS.md)
- [System Architecture](file:///c:/Users/OM/Desktop/Dreamteal/docs/ARCHITECTURE.md)
- [External Provider Integration Specification](file:///c:/Users/OM/Desktop/Dreamteal/docs/PROVIDER_INTEGRATION.md)
- [Data Model Specification](file:///c:/Users/OM/Desktop/Dreamteal/docs/DATA_MODEL.md)
- [API Contract Specification](file:///c:/Users/OM/Desktop/Dreamteal/docs/API_CONTRACT.md)
- [UI/UX Design System](file:///c:/Users/OM/Desktop/Dreamteal/docs/UI_DESIGN_SYSTEM.md)
- [Reaction-Based Review System](file:///c:/Users/OM/Desktop/Dreamteal/docs/REVIEW_SYSTEM.md)
- [Logging & Progress System](file:///c:/Users/OM/Desktop/Dreamteal/docs/LOGGING_SYSTEM.md)
- [Recommendation Engine Architecture](file:///c:/Users/OM/Desktop/Dreamteal/docs/RECOMMENDATION_SYSTEM.md)
- [Implementation Roadmap](file:///c:/Users/OM/Desktop/Dreamteal/docs/IMPLEMENTATION_ROADMAP.md)
- [Progress Tracker](file:///c:/Users/OM/Desktop/Dreamteal/docs/PROGRESS.md)
- [Changelog](file:///c:/Users/OM/Desktop/Dreamteal/docs/CHANGELOG.md)
