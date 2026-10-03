# DreamTeal Git & GitHub Development Workflow

## 1. Overview & Core Philosophy

Version control is an integral safety, audit, and memory mechanism for the DreamTeal platform. Because DreamTeal is developed iteratively by a solo developer paired with an advanced AI coding assistant, Git history serves as the authoritative timeline of architectural decisions, feature implementations, bug fixes, and verified milestones.

### Non-Negotiable Core Rules:
1. **Never work directly on `main`**: `main` represents verified, stable milestone releases only.
2. **Never destroy history**: Destructive commands (`git reset --hard`, `git push --force`, `git clean -fd`) are strictly prohibited unless explicitly requested by the user.
3. **Never commit real credentials**: Secrets (`SECRET_KEY`, `TMDB_ACCESS_TOKEN`, `RAWG_API_KEY`, passwords) must live exclusively in `.env` (ignored by Git) and `.env.example`.
4. **Documentation and code must stay synchronized**: Every code change that alters an API, model, or product behavior must update the relevant documentation in the same commit.
5. **No completion without verification and commit**: A task or phase is never declared complete until code, tests, documentation, commit, and push have succeeded.

---

## 2. Branch Strategy

DreamTeal adopts a lightweight, structured branching model tailored for rapid solo development paired with AI assistance:

```text
main (v0.4.1-alpha) ──────────────────────────● (Stable Milestones Only)
                      ▲                       │
                      │ merge on release      │
                      │                       ▼
develop ──────────────●───────────────────────● (Active Integration)
         ▲              ▲
         │ merge PR/feat │ merge PR/fix
         │              │
feature/xxx             fix/xxx (Short-lived topic branches)
```

### Branch Definitions:

| Branch Name | Purpose | Working Rules |
| :--- | :--- | :--- |
| **`main`** | Production-ready, stable milestone releases. | **Protected.** Never commit directly to `main`. Merges come only from `develop` upon completing and verifying a major phase. |
| **`develop`** | Active development integration branch. | Primary working branch where verified features and fixes are integrated. |
| **`feature/<name>`** | Individual feature or phase development (e.g. `feature/recommendation-engine`, `feature/provider-sync`). | Branched from `develop`. Merged back into `develop` when feature implementation and tests are complete. |
| **`fix/<name>`** | Targeted bug fixes (e.g. `fix/series-progress-field`, `fix/query-validation`). | Branched from `develop`. Merged back into `develop` with dedicated regression tests. |

---

## 3. Commit Message Policy

DreamTeal follows the **Conventional Commits** specification to ensure a clean, readable, and parseable commit history:

```text
<type>(<scope>): <short description in present tense>

[optional body explaining rationale, non-obvious context, or breaking changes]
```

### Types:
- **`feat`**: A new user-facing feature or API capability (e.g. `feat(catalog): add TMDB multi-mode discovery feeds`).
- **`fix`**: A bug fix or error correction (e.g. `fix(tracking): validate diary log month query parameter`).
- **`test`**: Adding missing tests or correcting test fixtures (e.g. `test(provider): add offline mock isolation tests`).
- **`docs`**: Documentation additions or updates (e.g. `docs(git): document branch strategy and commit policy`).
- **`refactor`**: Code restructuring without changing behavior or adding features (e.g. `refactor(matcher): extract confidence scoring rules`).
- **`chore`**: Maintenance, dependencies, settings, or `.gitignore` updates (e.g. `chore(deps): pin requirements.txt versions`).

### Rules:
- Keep the first line concise (under 72 characters).
- Do not commit giant monolithic bundles of unrelated work.
- Use imperative mood: `"add"`, not `"added"`; `"fix"`, not `"fixing"`.

---

## 4. Phase Completion Process & Gate

A major phase (e.g. Phase 1, Phase 2, Phase 3) is **NOT complete** simply because application code runs. Every phase must pass through the **Phase Completion Gate**:

```text
Step 1: Verification
  ├── python manage.py check (Zero issues)
  ├── python manage.py makemigrations --check (Zero pending migrations)
  └── python manage.py test (100% tests passing offline)
        │
        ▼
Step 2: Documentation Synchronization
  ├── Update docs/PROGRESS.md
  ├── Update docs/CHANGELOG.md
  └── Update all affected architecture and API specs
        │
        ▼
Step 3: Review Git Status & Diff
  ├── git status (Review all untracked/modified files)
  └── git diff --stat (Ensure no accidental files or secrets)
        │
        ▼
Step 4: Create Semantic Commit
  └── git commit -m "feat(phase-X): complete <phase description>"
        │
        ▼
Step 5: Tag Stable Milestone (on main)
  └── git tag -a vX.Y.Z-alpha -m "DreamTeal Milestone vX.Y.Z-alpha"
        │
        ▼
Step 6: Push to GitHub Remote
  ├── git push origin <branch>
  └── git push origin --tags
        │
        ▼
Step 7: Record Audit Trail in docs/PROGRESS.md
  └── Log commit hash, branch name, tag, and exact test results
```

---

## 5. Milestone Tagging Convention

DreamTeal uses semantic alpha version tags to demarcate verified project milestones:
- `v0.1.0-alpha`: Phase 0 Discovery & Initial Architectural Alignment.
- `v0.2.0-alpha`: Reaction Taxonomy & Progress Architecture Approval.
- `v0.3.0-alpha`: Phase 1 Backend Data Foundations & Initial Models.
- `v0.4.0-alpha`: Phase 2 Core REST API & External Metadata Provider Architecture.
- `v0.4.1-alpha`: Phase 2 Correction Pass (Discovery Semantics, Safe Fallback, Deduplication, Region Configuration, Offline Test Isolation).
- `v0.5.0-alpha`: *Upcoming* Phase 3 Recommendation Engine.

---

## 6. Secret Protection & Pre-Commit Verification

Before staging or committing changes, verify that no credentials or private environment variables are included:

### Prohibited Tracked Files:
- `.env`, `.env.local`, `.env.*`
- Local SQLite database files (`db.sqlite3`, `*.sqlite3`)
- Private API keys, access tokens, or real production passwords

### Safe Files Allowed:
- `.env.example` (Template with empty placeholders only)
- Public test fixtures with generic development credentials (`dreamteal_tester` / `dreamteal_pass123`)

---

## 7. AI Development Instructions

When an AI coding assistant interacts with this repository, it must adhere strictly to these principles:

1. **Treat Git as Project Memory**:
   - Inspect existing files, documentation, and Git status before writing new code.
   - Never assume the current prompt is starting from a blank slate.
2. **Preserve Working Implementations**:
   - Never discard working code or established architectural patterns without understanding the current state.
   - Refactor only when explicitly directed or strictly required.
3. **Synchronize Documentation Immediately**:
   - Whenever an implementation detail changes, update `PROGRESS.md`, `CHANGELOG.md`, and relevant specs within the same response.
4. **Enforce Non-Destructive Operations**:
   - Do not invoke destructive Git commands (`git reset --hard`, `git clean -fd`) without explicit confirmation.
5. **Always Report Git State**:
   - Every completed task report must clearly list the current branch, commit hash, files changed, and test status.
