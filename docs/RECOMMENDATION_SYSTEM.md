# DreamTeal In-House Recommendation Engine Specification

## 1. Goal & Core Purpose
A primary motivation behind DreamTeal is answering:
> *"I just finished/watched/read/played this item. What should I consume next?"*

Users discover their next movie, series, manga, or video game directly within DreamTeal without leaving for third-party platforms.

---

## 2. Core Architectural Principles
- **No Star Rating Dependency [APPROVED]**: Recommendations do not rely on numeric star averages or hidden numerical scores.
- **Deterministic & Rule-Based First [APPROVED]**: Uses verifiable metadata relationships (genres, tags, vibes, media cross-links) rather than unpredictable black-box ML, paid third-party APIs, or vector embeddings.
- **Cross-Category Recommendations [APPROVED]**: Supports matching across different media formats (e.g., recommending a cyberpunk game like *Cyberpunk 2077* to someone who watched *Severance* or *Blade Runner 2049*).
- **Honest Matching [APPROVED]**: Recommendations are derived from explicit data attributes. If evidence is weak, candidates are excluded rather than claiming artificial similarity.
- **100% Offline & Database-Backed**: Operates entirely over local `MediaItem` records; never triggers remote provider requests during recommendation computation.
- **Privacy & Ownership Guarantees**: Personalization uses only the requesting user's own tracking, diary, and review records. Other users' private information is strictly isolated and never exposed.

---

## 3. Implementation Architecture (`apps/recommendations/services.py`)

The engine is encapsulated in `apps.recommendations.services.RecommendationEngine` with configurable weights defined in `RecommendationWeights`:

$$\text{Score}(A, B) = w_t \cdot \text{VibeTagMatch}(A, B) + w_g \cdot \text{GenreMatch}(A, B) + w_c \cdot \text{CrossMediaLink}(A, B) + w_r \cdot \text{ReactionAffinity}(B)$$

### A. Scoring Signals & Provisional Weights

| Signal | Provisional Weight | Calculation Formula | Description & Match Explanation |
| :--- | :---: | :--- | :--- |
| **Vibe & Thematic Tag Match** | $w_t = 40.0$ | $\text{Jaccard}(T_A, T_B) = \frac{\|T_A \cap T_B\|}{\|T_A \cup T_B\|}$ | Matches specific thematic hooks (e.g. *Cyberpunk*, *Dark Fantasy*, *Neo-Noir*). Outputs e.g. `"Shares the Cyberpunk and Dystopian themes."` |
| **Normalized Genre Match** | $w_g = 30.0$ | $\text{Jaccard}(G_A, G_B) = \frac{\|G_A \cap G_B\|}{\|G_A \cup G_B\|}$ | Normalizes broad categories using the Jaccard index so broad genres do not overwhelm focused overlap. Outputs e.g. `"Shares Action and Sci-Fi genres."` |
| **Cross-Media / Franchise Link** | $w_c = 15.0$ | Discrete bonus ($15.0$ or $0.0$) | Evaluates verified franchise tags (`franchise-*`, `universe-*`, `star-wars`, `middle-earth`, `batman-universe`, etc.) or verified cross-category creator overlap. Generic themes (e.g. *Cyberpunk*, *Dystopian*) are thematic tags and never treated as franchise links. Outputs e.g. `"Part of the Batman universe."` |
| **Qualitative Reaction Affinity** | $w_r = 15.0$ | User preference bonus + Community consensus | Evaluates user positive reactions (`Peak`, `Loved It`, `Good Time`) as positive preference bonuses, treats `Not My Thing` as negative preference feedback against reviewed media's relevant genres/tags (without penalizing unrelated works), and factors community public verdicts without numeric averages. |
| **Minimum Evidence Threshold** | Threshold $= 15.0$ | $\text{Score}(A, B) \ge 15.0$ | Eliminates weak coincidental overlaps (e.g. sharing only 1 broad genre with 0 shared tags). |

### B. Deterministic Tie-Breaking
When candidates achieve identical scores, rankings are deterministically resolved in the following strict order:
1. Total score (descending)
2. Count of shared tags (descending)
3. Count of shared genres (descending)
4. Release year (descending, nulls last)
5. Title (alphabetical ascending)
6. Unique UUID identifier (ascending)

---

## 4. User Personalization & Exclusion Rules

### A. Excluded from "Next to Consume":
When the user is authenticated:
1. **Completed / Watched / Finished**: Items with status `WATCHED`, `COMPLETED`, or `FINISHED`.
2. **Actively in Progress**: Items with status `WATCHING`, `READING`, or `PLAYING`.
3. **Abandoned**: Items marked `DROPPED`.
4. **Paused**: Items marked `PAUSED`.
5. **Diary History**: Items with recorded session entries in `DiaryLog`.
6. **Rejected**: Items reviewed by the user with the qualitative `Skip` reaction (strictly an item-level exclusion; does not exclude other works sharing tags).

### B. Eligible Candidates:
1. **Unconsumed Catalog Works**: Clean discovery candidates the user has not yet tracked.
2. **Backlog Intentions**: Items marked `PLAN_TO_WATCH`, `PLAN_TO_READ`, or `BACKLOG` remain prime candidates when they match the base work.

### C. Negative Preference Feedback (`Not My Thing`):
- When a user reacts `Not My Thing` to a work, its specific genres and tags provide negative preference signals, penalizing related candidates that share those attributes.
- Unrelated candidates sharing none of the disliked genres/tags receive zero penalty.
- Disliking one title in a franchise does not remove franchise relationship points for another title.

### D. Anonymous Discovery:
When unauthenticated (`user=None`), exclusions and personal affinity are bypassed, returning general content-based and community-praised recommendations.

---

## 5. API Contract (`GET /api/v1/recommendations/next/<slug>/`)

- **Method**: `GET`
- **Permissions**: `AllowAny` (supports both anonymous and authenticated callers)
- **Query Parameters**:
  - `cross_category` (boolean, default `true`): If `false`, restricts results to candidates matching the source media's `media_type`.
  - `category` (string, optional): Explicit target category filter (`MOVIE`, `SERIES`, `MANGA`, `MANHWA`, `GAME`).
  - `limit` (integer, default `10`, min `1`, max `50`): Maximum recommendations returned.
  - `include_scores` (boolean, default `false`, diagnostic only): Includes internal similarity score breakdown; strictly restricted to `DEBUG=True` mode or authenticated staff users in production.

### Sample Response Envelope (200 OK):
```json
{
  "base_media": {
    "id": "aa5e8458-344b-4f0d-84cd-c0f0bfae4e8f",
    "slug": "severance-2022",
    "title": "Severance",
    "media_type": "SERIES"
  },
  "recommendations": [
    {
      "id": "bb9f1234-5678-4a1b-9c2d-3e4f5a6b7c8d",
      "slug": "cyberpunk-2077-2020",
      "title": "Cyberpunk 2077",
      "media_type": "GAME",
      "poster_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=500",
      "release_year": 2020,
      "match_reasons": [
        "Shares the Dystopian theme.",
        "Shares the Sci-Fi genre."
      ]
    }
  ],
  "count": 1,
  "filters": {
    "cross_category": true,
    "category": null,
    "limit": 10
  }
}
```

---

## 6. Known Limitations & Future Extensibility
1. **Franchise Relationship Model**: DreamTeal does not currently have a standalone `Franchise` model or M2M table. Cross-media adaptation detection currently uses explicit universe/franchise tags (`KNOWN_FRANCHISE_IDENTIFIERS`, `franchise-*`, `universe-*`) and verified creator overlaps across category extension models (`movie_detail.director`, `game_detail.developer`, `manga_detail.author`). Generic themes (e.g. *Cyberpunk*, *Dark Fantasy*) are thematic tags and are never treated as franchises. The `RecommendationEngine.check_cross_media_relationship` method provides a clean extension hook for future franchise models.
2. **Cold Start on Sparse Metadata**: If a source item has zero genres and zero tags, similarity cannot be calculated with confidence; the engine cleanly returns an empty list (`[]`) rather than fabricating fake suggestions.
