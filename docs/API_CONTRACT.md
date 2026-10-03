# DreamTeal API Contract Specification

This document defines the REST API endpoints provided by the Django backend. All requests and responses use standard JSON envelopes without any star-rating attributes.

---

## 1. Authentication & Session Endpoints (Django Session + CSRF) [APPROVED]

### `GET /api/v1/users/csrf/`
- **Description**: Sets the CSRF cookie (`csrftoken`) in the browser and returns the token value for client state initialization.
- **Response (200 OK)**:
  ```json
  {
    "csrftoken": "abcd1234efgh5678..."
  }
  ```

### `POST /api/v1/users/login/`
- **Description**: Authenticate user credentials and establish a Django session (`sessionid` HTTP-only cookie).
- **Request Headers**: `X-CSRFToken: <token>`
- **Request Payload**:
  ```json
  {
    "username": "tester",
    "password": "correct_password"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "user": {
      "id": 1,
      "username": "tester",
      "email": "tester@example.com",
      "display_name": "Tester"
    }
  }
  ```

### `POST /api/v1/users/logout/`
- **Description**: Invalidate the active Django session.
- **Request Headers**: `X-CSRFToken: <token>`
- **Response**: `200 OK` (`{"detail": "Successfully logged out."}`)

### `GET /api/v1/users/me/`
- **Description**: Retrieve active authenticated user profile.
- **Response (200 OK)**: Current user object or `401 Unauthorized` if unauthenticated.

---

## 2. Catalog & Discovery Endpoints

### `GET /api/v1/media/`
- **Description**: Browse and search catalog media items across all categories or filtered by category/genre/tag.
- **Query Params** (Validated with `MediaListQuerySerializer`):
  - `category` or `media_type`: `MOVIE` | `SERIES` | `MANGA` | `GAME`
  - `search` or `q`: String search query
  - `genre`: Slug
  - `tag`: Slug
  - `ordering`: `-release_year` | `release_year` | `title` | `-title` | `-created_at` | `created_at`
- **Response**: `200 OK` paginated list.

### `GET /api/v1/media/<slug>/`
- **Description**: Detailed metadata for a single media item including media-type specific extension models and external provider mappings.
- **Response**: `200 OK` or `404 Not Found`.

### `GET /api/v1/media/search/`
- **Description**: Search across metadata providers with balanced category interleaving. Enriched with local import status (`is_imported: true/false`, `slug`).
- **Query Params** (Validated with `MediaSearchQuerySerializer`):
  - `q`: Search string
  - `category`: `MOVIE` | `SERIES` | `MANGA` | `MANHWA` | `GAME` (optional)
  - `limit`: Integer (1 to 50, default 20)
- **Response**: `200 OK` with `results` array.
- **Error (400 Bad Request)**: Returned if `limit` is not an integer or `category` is invalid.

### `GET /api/v1/discovery/<category>/`
- **Description**: Multi-mode discovery feeds (Movies, Series, Manga, Manhwa, Games).
- **URL Param**: `category` (`movies` | `series` | `manga` | `manhwa` | `games`)
- **Query Params** (Validated with `DiscoveryQuerySerializer`):
  - `mode`: `popular` | `latest` | `trending` | `upcoming` (default `popular`)
  - `limit`: Integer (1 to 50, default 20)
- **Response**: `200 OK` with candidate `results` array.
- **Error (400 Bad Request)**: Returned if `mode`, `category`, or `limit` are invalid.

### `POST /api/v1/media/import/`
- **Description**: On-demand import of external media items into DreamTeal's catalog with safe cross-provider deduplication.
- **Request Payload**:
  ```json
  {
    "provider": "tmdb",
    "external_id": "157336",
    "media_type": "MOVIE",
    "title_hint": "Interstellar",
    "force_refresh": false
  }
  ```
- **Response Lifecycle**:
  - `201 Created`: When a brand new `MediaItem` catalog record is created.
  - `200 OK`: When the work already exists (either through prior import or via cross-provider deduplication) and is returned/refreshed.
- **Error Handling**: `400 Bad Request` on invalid payload, `404 Not Found` if provider cannot find item.

### `GET /api/v1/catalog/providers/`
- **Description**: List active external metadata providers and data-driven legal attribution notices.
- **Response**: `200 OK` with `results` array.


---

## 3. User Tracking Endpoints (Strict Create vs Update)

### `POST /api/v1/tracking/status/`
- **Description**: Set initial user status for a media item.
- **Response**: `201 Created` with created status object.
- **Error**: `409 Conflict` if status already exists for this media item (client should use `PATCH`).
- **Request Payload**:
  ```json
  {
    "media_id": "uuid-1234",
    "status": "WATCHING",
    "is_favorite": false
  }
  ```

### `PATCH /api/v1/tracking/status/<status_id>/`
- **Description**: Update existing status or favorite flag.
- **Response**: `200 OK` with updated status object.
- **Request Payload**:
  ```json
  {
    "status": "COMPLETED",
    "is_favorite": true
  }
  ```

---

## 4. Category-Specific User Progress Endpoints [APPROVED]

### `POST /api/v1/tracking/progress/`
- **Description**: Initialize progress tracking for a media item.
- **Response**: `201 Created`.
- **Error**: `409 Conflict` if progress record already exists.

### `PATCH /api/v1/tracking/progress/<progress_id>/`
- **Description**: Update category-specific progress counters.
- **Response**: `200 OK`.
- **Request Payload** (Series Progress):
  ```json
  {
    "series_progress": {
      "current_season": 2,
      "current_episode": 5,
      "last_watched_episode_title": "The Trap"
    }
  }
  ```
- **Request Payload** (Manga Progress):
  ```json
  {
    "manga_progress": {
      "current_chapter": 142,
      "current_volume": 12
    }
  }
  ```
- **Request Payload** (Game Progress):
  ```json
  {
    "game_progress": {
      "hours_played": 34.5,
      "completion_type": "MAIN_STORY",
      "platform_played_on": "PC"
    }
  }
  ```

---

## 5. History-Preserving Diary Log Endpoints (With Automatic Progress Sync) [APPROVED]

### `POST /api/v1/tracking/logs/`
- **Description**: Create a new history-preserving diary entry recording a specific consumption session.
- **Synchronization Rules**:
  - Automatically advances current progress forward by default (`sync_progress: true`).
  - Historical non-reversal: past sessions will not regress active progress.
  - Set `"sync_progress": false` to bypass automatic active progress updates.
- **Response**: `201 Created` with created diary record and updated progress status.
- **Request Payload** (Example TV Series Session):
  ```json
  {
    "media_id": "uuid-1234",
    "logged_date": "2026-10-03",
    "is_rewatch_or_replay": false,
    "session_notes": "Watched the mid-season finale.",
    "progress_snapshot": { "season": 2, "episode": 5 },
    "sync_progress": true
  }
  ```
- **Request Payload** (Example Game Session):
  ```json
  {
    "media_id": "uuid-9012",
    "logged_date": "2026-10-03",
    "is_rewatch_or_replay": false,
    "session_notes": "Completed side quests in sector 7.",
    "progress_snapshot": { "session_hours": 2.5, "completion_type": null },
    "sync_progress": true
  }
  ```

### `GET /api/v1/tracking/logs/`
- **Description**: Fetch user diary history formatted in chronological timeline entries.
- **Query Params**:
  - `media_id`: Filter logs for a specific media item.
  - `year`: Filter by consumption year.
  - `month`: Filter by consumption month.
- **Response Envelope (200 OK)**:
  ```json
  {
    "count": 15,
    "results": [
      {
        "id": "uuid-log-001",
        "media_item": {
          "id": "uuid-1234",
          "title": "The Batman",
          "poster_url": "/media/posters/the-batman.jpg",
          "release_year": 2022
        },
        "logged_date": "2026-10-02",
        "is_rewatch_or_replay": false,
        "session_notes": "Watched climax scene in theater.",
        "progress_snapshot": { "season": 1, "episode": 8 },
        "created_at": "2026-10-02T22:15:00Z",
        "updated_at": "2026-10-02T22:15:00Z"
      }
    ]
  }
  ```

### `GET /api/v1/tracking/logs/<log_id>/`
- **Description**: Retrieve a single diary log entry.
- **Response**: `200 OK`.

### `PATCH /api/v1/tracking/logs/<log_id>/`
- **Description**: Controlled editing of a specific historical diary log entry.
- **Editable Fields**: `logged_date`, `is_rewatch_or_replay`, `session_notes`, `progress_snapshot`.
- **Response**: `200 OK` with updated diary record.
- **Request Payload**:
  ```json
  {
    "session_notes": "Corrected note: Watched IMAX re-release.",
    "logged_date": "2026-10-03"
  }
  ```

### `DELETE /api/v1/tracking/logs/<log_id>/`
- **Description**: Delete a specific historical diary log entry without affecting other past entries.
- **Response**: `204 No Content`.

---

## 6. Review & Universal Reaction Endpoints [APPROVED]

### `GET /api/v1/reviews/reactions/`
- **Description**: List all active universal qualitative reaction definitions. Badges are rendered via typography, text labels, and design tokens (no emojis or generic icon sets).
- **Response Envelope (200 OK)**:
  ```json
  [
    {
      "id": "uuid-badge-1",
      "key": "peak",
      "display_name": "Peak",
      "color_token": "electric-gold",
      "description": "An exceptional experience that the user strongly recommends.",
      "sort_order": 1
    },
    {
      "id": "uuid-badge-2",
      "key": "loved_it",
      "display_name": "Loved It",
      "color_token": "warm-coral",
      "description": "A genuinely enjoyable experience that the user highly values.",
      "sort_order": 2
    },
    {
      "id": "uuid-badge-3",
      "key": "good_time",
      "display_name": "Good Time",
      "color_token": "radiant-teal",
      "description": "Enjoyable and worth experiencing, but not exceptional.",
      "sort_order": 3
    },
    {
      "id": "uuid-badge-4",
      "key": "not_my_thing",
      "display_name": "Not My Thing",
      "color_token": "muted-lavender",
      "description": "The user did not connect with it, even if the media may have strengths.",
      "sort_order": 4
    },
    {
      "id": "uuid-badge-5",
      "key": "skip",
      "display_name": "Skip",
      "color_token": "crimson",
      "description": "The user would not recommend spending time on it.",
      "sort_order": 5
    }
  ]
  ```

### `POST /api/v1/reviews/`
- **Description**: Create a new qualitative review for a media item.
- **Response**: `201 Created` with created review.
- **Error Handling**: `409 Conflict` if the user already reviewed this item.
- **Request Payload**:
  ```json
  {
    "media_id": "uuid-1234",
    "reaction_key": "peak",
    "review_text": "Incredible atmosphere and score. A modern detective standout.",
    "contains_spoilers": false,
    "is_public": true
  }
  ```

### `GET /api/v1/reviews/<review_id>/`
- **Description**: Retrieve a single review by ID with strict privacy access controls.
- **Privacy Access Rules**:
  - `is_public: true`: Returns `200 OK` for any caller (anonymous or authenticated).
  - `is_public: false`:
    - Owning authenticated user: Returns `200 OK`.
    - Other authenticated user or unauthenticated caller: Returns `404 Not Found`.

### `PATCH /api/v1/reviews/<review_id>/`
- **Description**: Update an existing review.
- **Editable Fields**: `reaction_key`, `review_text`, `contains_spoilers`, `is_public`.
- **Response**: `200 OK` with updated review.
- **Request Payload**:
  ```json
  {
    "reaction_key": "loved_it",
    "review_text": "Updated critique with second viewing thoughts.",
    "contains_spoilers": true
  }
  ```

### `DELETE /api/v1/reviews/<review_id>/`
- **Description**: Delete a user review.
- **Response**: `204 No Content`.

### `GET /api/v1/reviews/?media=<media_id>`
- **Description**: List public reviews for a specific media item.
- **Response**: `200 OK` paginated list.

---

## 7. Recommendation Endpoints

### `GET /api/v1/recommendations/next/<slug>/`
- **Description**: Get "What to consume next" recommendations based on a given media item using deterministic matching.
- **Query Params**:
  - `cross_category`: `true` | `false`
- **Response Payload (200 OK)**:
  ```json
  {
    "base_media": "The Batman",
    "recommendations": [
      {
        "id": "uuid-9999",
        "title": "Cyberpunk 2077",
        "media_type": "GAME",
        "match_reason": "Matches dark neo-noir vibe & crime thriller themes",
        "poster_url": "/media/posters/cyberpunk.jpg"
      }
    ]
  }
  ```
