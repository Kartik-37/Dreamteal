# DreamTeal In-House Recommendation Engine Specification

## 1. Goal & Core Purpose
A primary motivation behind DreamTeal is answering:
> *"I just finished/watched/read/played this item. What should I consume next?"*

Users should discover their next movie, series, manga, or game directly within DreamTeal without leaving for third-party platforms.

---

## 2. Recommendation Principles
- **No Star Rating Dependency [APPROVED]**: Recommendations do not rely on numeric star averages.
- **Deterministic & Rule-Based First [APPROVED]**: Uses verifiable metadata relationships (genres, tags, vibes, media cross-links) rather than unpredictable black-box ML.
- **Cross-Category Recommendations [APPROVED]**: Supports matching across different media formats (e.g. recommending a cyberpunk game like *Cyberpunk 2077* to someone who enjoyed the anime *Ghost in the Shell*).
- **Honest Matching [APPROVED]**: Recommendations are derived from explicit data attributes rather than simulated fake scores.
- **Scoring Formula [PROVISIONAL]**: The exact scoring calculation is a technical proposal subject to experimentation.
- **Scoring Weights [NOT FINALIZED]**: The relative numeric weights for genres, tags, cross-media links, and user reaction affinity are not finalized and will be configured as tunable engine parameters.

---

## 3. Provisional Recommendation Scoring Model

The deterministic engine evaluates candidate items $B$ against a target item $A$ using a weighted similarity model:

$$\text{Score}(A, B) = w_g \cdot \text{GenreMatch}(A, B) + w_t \cdot \text{VibeTagMatch}(A, B) + w_c \cdot \text{CrossMediaLink}(A, B) + w_r \cdot \text{ReactionAffinity}(B)$$

### Candidate Variables & Provisional Weight Definitions:
- $\text{GenreMatch}(A, B)$: Overlap of shared genre taxonomy between items. Weight $w_g$ is **provisional and not finalized**.
- $\text{VibeTagMatch}(A, B)$: Overlap of shared thematic tags and aesthetic vibes (e.g. "Cyberpunk", "Cozy", "Mind-Bending"). Weight $w_t$ is **provisional and not finalized**.
- $\text{CrossMediaLink}(A, B)$: Discrete bonus for items in the same pop-culture franchise or cross-media adaptation (e.g., Manga adaptation of an Anime series, or Game set in the same universe). Weight $w_c$ is **provisional and not finalized**.
- $\text{ReactionAffinity}(B)$: Bonus weighting based on positive community reaction verdicts for candidate $B$ (e.g. items heavily marked with ⚡ *Peak* or 💎 *Loved It*). Weight $w_r$ is **provisional and not finalized** (qualitative reaction counts are used directly without any internal star mapping).

*Architectural Requirement*: Weights will be maintained in a backend configuration dictionary rather than hardcoded in SQL or view logic, allowing tuning without database migrations or code rewrites.

---

## 4. UI Integration
- **Media Detail Page**: "What to Watch/Read/Play Next" horizontal poster carousel.
- **Explore / Discovery Hub**: Interactive Vibe Filter ("I want something: [Dark Fantasy] + [Cyberpunk] + [Quick Read/Play]").
- **Post-Log Prompt**: When marking media as `Watched` / `Completed` / `Finished`, the logging modal presents a "What's Next?" recommendation preview.
