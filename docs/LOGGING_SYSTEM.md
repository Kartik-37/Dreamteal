# DreamTeal Logging & Progress Architecture

## 1. Overview & Core Philosophy
In DreamTeal, **Logging** is treated as a core feature rather than a minor add-on.

The platform explicitly separates:
1. **Media Status**: Where media sits in a user's catalog (`Plan to Watch`, `Watching`, `Completed`, `Dropped`).
2. **Current Progress**: The user's active progress counter (`Season 2 Ep 5`, `Chapter 140`, `45 Hours Played`), proposed as category-specific models (`SeriesProgress`, `MangaProgress`, `GameProgress`).
3. **Diary Log**: **History-preserving diary records that users can edit through controlled log editing**.
4. **Review**: The qualitative verdict reaction badge and written critique.

---

## 2. History-Preserving Diary Records & Controlled Editing [APPROVED]

### 2.1 Core Principle
A diary entry must preserve historical consumption activity. Rather than being an immutable black box, diary entries support **controlled log editing** so users can correct typos, dates, and session progress while strictly protecting the integrity of historical consumption data.

### 2.2 Controlled Log Editing Specifications
- **Editable Fields**:
  - `logged_date`: The user-specified date when the consumption occurred.
  - `is_rewatch_or_replay`: Flag indicating whether this session was a rewatch, re-read, or replay.
  - `session_notes`: User commentary or quick note for this specific session.
  - `progress_snapshot`: Progress reached during this session (e.g. `{"season": 2, "episode": 5}`, `{"chapter": 142}`, `{"hours_spent": 3.5}`).
- **Audit & Identity Fields (Non-Editable)**:
  - `id`: Unique UUID primary key.
  - `user`: Owning user.
  - `media_item`: Associated catalog media item.
  - `created_at`: Immutable timestamp recording when the record was initially created.
  - `updated_at`: Automatically updated whenever controlled editing occurs.

### 2.3 Individual Record Preservation & Anti-Collapsing Safeguards
- Every consumption event creates its own discrete `DiaryLog` record with a unique UUID.
- Editing a diary log targets **only that specific record** by its primary key via `PATCH /api/v1/tracking/logs/<id>/`.
- Controlled editing **never** overwrites, merges, or collapses other historical entries.
- Logging a new session never clobbers existing history.

### 2.4 Representation of Rewatches, Re-reads, and Replays
- Each rewatch, re-read, or replay generates a **new, separate `DiaryLog` record** with `is_rewatch_or_replay = True`.
- In the Letterboxd-style diary timeline, all sessions appear chronologically as distinct entries, decorated with a rewatch/replay indicator (`🔁`).
- The user's total watch/read/play count for an item is dynamically computed from the count of historical diary entries.

### 2.5 Deletion Semantics
- Deleting a diary entry (`DELETE /api/v1/tracking/logs/<id>/`) removes **only that specific session record** from the user's historical log timeline.
- It does **not** delete the media item from the catalog.
- It does **not** erase or mutate other historical diary entries for that media item.
- It does **not** reset the overall `UserMediaStatus` unless explicitly requested or if no further log activity remains.

### 2.6 Automatic Diary → Progress Synchronization [APPROVED]
- **Default Behavior**: When a user logs a diary entry, the active `UserMediaProgress` (and its category extension: `SeriesProgress`, `MangaProgress`, or `GameProgress`) is updated automatically.
- **Forward Progress Rule**:
  - *TV Series*: If current progress is S2E3 and the diary log is for S2E4, active progress advances to S2E4.
  - *Manga/Manhwa*: If current chapter is 80 and the diary log is for Chapter 84, active progress advances to 84.
  - *Video Games*: If current hours played is 12.0 and the diary session records 2.5 hours, active hours become 14.5.
- **Historical Non-Reversal Rule (Strict Safeguard)**:
  - Historical diary entries must NEVER accidentally regress active progress.
  - Example: If current progress is Season 2 Episode 8, and the user enters a retrospective diary log for Season 2 Episode 4, the diary log is saved with Episode 4, but current progress remains at Episode 8.
  - Example: If current manga progress is Chapter 84, and the user logs a forgotten session for Chapter 70, current progress remains at 84.
- **Game Hours Aggregation Lifecycle**:
  - Diary sessions are the source of truth for session-based gameplay.
  - `GameProgress.hours_played` is maintained consistently across all operations via transaction-safe model hooks:
    - **Creation**: Session hours (`session_hours`) are atomically added to `GameProgress.hours_played`, and recorded in `progress_snapshot['_synced_hours']`.
    - **Editing**: Modifying session hours (e.g. 2.5h -> 5.0h) computes the delta (`+2.5h`) and applies it cleanly without double-counting.
    - **Deletion**: Deleting a session deducts its previously synced hours (`_synced_hours`) from `GameProgress.hours_played` (floored at `0.0`).
    - **Multiple Sessions**: Accumulate additively and decrement independently upon individual deletion.
    - **Opt-Out (`sync_progress=False`)**: When a log is saved with `sync_progress=False`, hours are recorded as unsynced (`_synced_hours = '0.0'`) and do not alter `GameProgress` on creation, update, or deletion.
  - If a diary log includes a game completion status (`Main Story`, `Main + Extra`, `100% Completionist`), `GameProgress.completion_type` is updated and `UserMediaStatus` can transition to `Finished`.
- **Optional Opt-Out**: The logging UI modal and API request include an optional toggle/parameter (`sync_progress: false`) for edge cases where the user does not want active progress to be updated, but automatic synchronization (`sync_progress: true`) is the default.

---

## 3. Category-Specific Logging Mechanics

### 3.1 Movies
- **Status States**: `Plan to Watch`, `Watching`, `Watched`, `Dropped`.
- **Log Parameters**: Log date, Rewatch indicator (`is_rewatch_or_replay`), optional session note.
- **Rewatch History**: Each rewatch generates a distinct `DiaryLog` row.

### 3.2 TV Series
- **Status States**: `Plan to Watch`, `Watching`, `Completed`, `Paused`, `Dropped`.
- **Progress Counter**: `current_season`, `current_episode` (via `SeriesProgress`).
- **Log Parameters**: Log date, episode snapshot (`Season S, Ep E`), Rewatch toggle, session note.

### 3.3 Manga / Manhwa / Webtoons
- **Status States**: `Plan to Read`, `Reading`, `Completed`, `Paused`, `Dropped`.
- **Progress Counter**: `current_chapter`, `current_volume` (via `MangaProgress`).
- **Log Parameters**: Log date, chapter milestone reached in session (`Ch 120`), Re-read toggle, session note.

### 3.4 Video Games
- **Status States**: `Backlog`, `Playing`, `Finished`, `Paused`, `Abandoned`.
- **Progress Counter**: `hours_played`, `completion_type` (`Main Story`, `Main + Extra`, `100% Completionist`) (via `GameProgress`).
- **Log Parameters**: Log date, hours played in session (e.g. `+4.5 hrs`), completion status update, Replay toggle, session note.

---

## 4. Letterboxd-Style Diary View UI
- Grouped chronologically by Year, Month, and Day.
- Features date badge block on the left (e.g. `OCT 2026 / 02`).
- Line-item row with media poster thumbnail, title, release year, rewatch icon (`🔁`), progress snapshot, and quick edit trigger.
- Clicking the edit trigger opens the controlled edit modal for that specific log entry.
