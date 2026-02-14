# Actions: Implementation Breakdown

Each action is a self-contained chunk suitable for an agentic LLM to complete in one session. Actions are ordered by dependency — later actions build on earlier ones. Each action specifies what to build, what it depends on, and how to verify it works.

---

## Third-Party Dependency Justification

The project guidelines say "use built-ins before third-party." The dependencies below are explicit exceptions where Django built-ins are insufficient or where the security/research-integrity stakes justify a dedicated library. Do not add further third-party packages without a similar justification.

| Package | Why not a built-in? | Justification |
|---------|---------------------|---------------|
| `django-allauth` | Django's auth has no social login | Mandated by guidelines. Google + GitHub OAuth. |
| `django-hijack` | No built-in impersonation | Mandated by guidelines. Admin user impersonation with safety banner. |
| `django-crispy-forms` + `crispy-bulma` | Django forms don't render Bulma markup | Mandated by guidelines. Consistent form styling. |
| `django-huey` | No built-in task queue | Mandated by guidelines (and "no Celery"). |
| `django-csp` | Django has no CSP middleware | Loading Pyodide + chart libs from CDN requires a properly configured CSP. Hand-rolling CSP headers is error-prone. |
| `django-ratelimit` | No built-in rate limiting | Auth and submission endpoints are abuse targets. Django's cache framework alone doesn't provide decorator-level rate limiting. |
| `django-simple-history` | Django admin log is append-only, no field diffs | Consent documents and survey questions are research instruments — auditable change history is an ethics requirement. |
| `django-recaptcha` / `django-turnstile` | No built-in CAPTCHA | Registration-only. Lightweight bot friction for a public-facing study. |
| `markdown` + `bleach` (or `nh3`) | No built-in markdown rendering or sanitisation | Consent docs and challenge descriptions are admin-authored markdown. Unsanitised markdown → XSS. |
| `pyarrow` | No built-in Parquet support | Dataset export to Parquet for research reproducibility. |
| `python-json-logger` | Django's logging is plain text | Structured JSON logs are needed for production log aggregation. |
| `django-solo` (or equivalent) | No built-in singleton model | `StudyConfig` needs exactly one row. Prevents accidental duplicates. |

**Django built-ins used where sufficient:** caching (cache framework), permissions/groups, logging (configured via `LOGGING` dict), sessions, CSRF, ORM constraints, admin, signals.

---

## Phase 0: Project Scaffolding

### Action 0.1 — Django Project Setup
**Depends on:** nothing
**Description:** Initialise the Django project with environment-based settings and core dependencies.
- Run `django-admin startproject config .` (or equivalent).
- Configure `settings.py`: split into `base.py`, `local.py`, `production.py`. Use env vars for `SECRET_KEY`, `DATABASE_URL`, `DEBUG`, `ALLOWED_HOSTS`.
- **Database config (per guidelines):**
  - `base.py`: no database defined (or a minimal default that `local.py`/`production.py` override).
  - `local.py`: **SQLite** (`db.sqlite3`) — no PostgreSQL dependency for local dev.
  - `production.py`: **PostgreSQL** via `DATABASE_URL` env var, using `dj-database-url` or `django-environ`.
  - Note: Django's `JSONField` and `CheckConstraint` work on both SQLite (3.38+) and PostgreSQL, so the split is safe.
- **Pages app + base template architecture:**
  - Create the `pages` app.
  - Create `pages/templates/pages/base.html` with: Bulma CSS (via CDN), htmx (via CDN), skip-to-content link, semantic HTML structure (`<nav>`, `<main>`, `<footer>`), `{% block content %}`, CSRF token, `{% block extra_js %}`.
  - Create `pages/templates/pages/navbar.html` (included in base): responsive Bulma navbar with login/logout links, user display name. Include a placeholder `{% block hijack_banner %}` for the hijack warning bar (populated in Action 0.4).
  - Create `pages/templates/pages/footer.html` (included in base).
  - Create `pages/templates/pages/messages.html` — Django messages display using Bulma notification classes.
  - All other apps extend `pages/base.html` (per guidelines).
- Add a simple health-check view at `/` that renders "Hello world" to confirm everything works.
- **Verify:** `uv run python manage.py runserver` starts, `/` returns 200, `uv run python manage.py migrate` runs cleanly on SQLite. Navbar renders. Messages display.

### Action 0.2 — Dependency and Tooling Baseline (uv)
**Depends on:** nothing (can run in parallel with 0.1)
**Description:** Establish the dependency management, quality gates, and development workflow using `uv`.
- Define all dependencies in `pyproject.toml` (not `requirements.txt`). Core deps: Django, django-allauth, django-huey, django-crispy-forms, crispy-bulma, django-environ (or python-dotenv), pyarrow. Dev deps: ruff, mypy, pytest, pytest-django, django-stubs.
- Add `psycopg2-binary` as a production-only dependency (not needed for local SQLite dev).
- Configure Ruff in `pyproject.toml`:
  - Enable rules: `E`, `F`, `W`, `I` (isort), `UP` (pyupgrade), `B` (bugbear), `S` (bandit subset), `SIM`.
  - **Enforce no catch-all exceptions** (per guidelines): enable `E722` (bare `except:`), `BLE001` (`except Exception:`). Set both as errors, not warnings.
  - Line length: 120 chars.
  - Target Python 3.13 (matches the project runtime).
- Configure mypy in `pyproject.toml`: strict mode, django-stubs plugin.
- Configure pytest in `pyproject.toml`: `DJANGO_SETTINGS_MODULE = "config.settings.local"`.
- Add a `Makefile` or `scripts` section in `pyproject.toml` with common commands:
  - `uv run python manage.py <command>` for Django management
  - `uv run ruff check .` for linting
  - `uv run pytest` for tests
- **Verify:** `uv sync` installs all deps. `uv run ruff check .` passes on the empty project. `uv run pytest` discovers and runs (zero tests is OK). A deliberate bare `except:` triggers a Ruff error.

### Action 0.3 — Authentication (django-allauth)
**Depends on:** 0.1, 0.2
**Description:** Set up django-allauth with Google and GitHub social login, plus email/password fallback.
- Install and configure django-allauth in settings (add to `INSTALLED_APPS`, `AUTHENTICATION_BACKENDS`, `MIDDLEWARE`).
- Configure allauth to require email verification (`ACCOUNT_EMAIL_VERIFICATION = "mandatory"`).
- Add Google and GitHub as social providers in settings. Use env vars for client IDs / secrets.
- Create allauth URL includes in `urls.py`.
- Override allauth templates to use Bulma styling and extend `base.html`.
- **Verify:** Registration, login, logout work via email/password. Social login config is present (full testing requires provider credentials). Email verification flow works (can use console email backend for local dev).

### Action 0.4 — Admin Impersonation (django-hijack)
**Depends on:** 0.3
**Description:** Set up django-hijack so admins can impersonate any user for debugging and support.
- Install `django-hijack`. Add to `INSTALLED_APPS` and `MIDDLEWARE`.
- Configure permissions: only superusers and staff with explicit `hijack` permission can impersonate.
- Enable the admin integration: add a "Hijack" button on the user list and user detail pages in Django admin.
- Add the hijack notification banner to `pages/templates/pages/base.html` — a visible warning bar (e.g. bright yellow) shown during hijacked sessions so it's never mistaken for a real user session. Include the "Release" button to end impersonation.
- Configure hijack URL includes in `urls.py`.
- **Verify:** Superuser can hijack a regular user from the admin. Banner appears during hijacked session. "Release" returns to admin. Non-superuser staff without permission cannot hijack.

### Action 0.5 — Django App Structure
**Depends on:** 0.1
**Description:** Create the Django apps that will house the models. Keep apps focused and minimal.
- `accounts` — Participant model, profile views.
- `consent` — ConsentDocument, ConsentRecord, OptionalConsentRecord.
- `surveys` — SurveyQuestion, SurveyResponse (the unified question system).
- `challenges` — Challenge, ChallengeAttempt, session logic.
- `sessions` — Session model, session orchestration views.
- `dashboard` — Personal results, front-page aggregate views.
- `pages` — Static/semi-static pages (landing, about, sponsors, contact, get-involved).
- Register all apps in `INSTALLED_APPS`.
- **Verify:** `uv run python manage.py check` passes. No models yet — just the app directories and empty files.

### Action 0.6 — Security Baseline (CSP, Rate Limiting, Markdown Sanitisation)
**Depends on:** 0.1
**Description:** Set up security infrastructure that affects template structure and middleware early.
- **Content Security Policy (CSP):**
  - Install `django-csp`. Configure in `base.py`.
  - `script-src`: `'self'`, Pyodide CDN origin, chart library CDN origin (Chart.js or Plotly.js). No `'unsafe-inline'` — use nonces via `{% csp_nonce %}` for inline scripts.
  - `worker-src`: `'self'`, `blob:` (Pyodide Web Worker).
  - `connect-src`: `'self'` (for HTMX and API fetches).
  - `style-src`: `'self'`, Bulma CDN origin, `'unsafe-inline'` (Bulma requires this for some utilities).
  - `img-src`: `'self'`, `data:` (for chart exports).
  - Document CSP origins in a comment block in settings so future CDN changes are easy.
- **Rate limiting:**
  - Install `django-ratelimit`.
  - Apply rate limits to abuse-prone endpoints: allauth login/register (5/minute per IP), consent POST (10/minute per user), session start (3/minute per user), attempt submission (10/minute per user).
  - Return `429 Too Many Requests` with a Bulma-styled error page.
- **Markdown rendering and sanitisation:**
  - Install `markdown` and `bleach` (or `nh3`).
  - Create a template filter `|render_markdown` that: converts markdown to HTML via `markdown` library, then sanitises with an allowlist of safe tags (`p`, `h1`–`h6`, `ul`, `ol`, `li`, `strong`, `em`, `a`, `code`, `pre`, `blockquote`, `br`, `hr`, `table`, `thead`, `tbody`, `tr`, `th`, `td`). No raw HTML passthrough — admin markdown is sanitised the same way.
  - Use this filter for: consent document bodies, challenge descriptions, survey question help text.
  - **No `|safe` filter** on any user-facing or admin-authored content without going through `|render_markdown`.
- **Bot friction:**
  - Install `django-recaptcha` (or `django-turnstile` for Cloudflare Turnstile). Configure with env vars.
  - Add CAPTCHA to the registration form only (not login — allauth's email verification handles most abuse). Can be made conditional (only shown after N failed attempts) in a later iteration.
- **Verify:** CSP headers are present in responses. Inline script without nonce is blocked by CSP. Rate-limited endpoint returns 429 after threshold. Markdown with `<script>` tag is sanitised to plain text. CAPTCHA renders on registration.

---

## Phase 1: Core Models

### Action 1.1 — Participant Model
**Depends on:** 0.3, 0.5
**Description:** Create the `Participant` model linked to Django's `User`.
- Fields: `user` (OneToOneField → User), `has_active_consent` (BooleanField, default False), `profile_completed` (BooleanField, default False), `profile_updated_at` (DateTimeField, nullable), `withdrawn_at` (DateTimeField, nullable — set on withdrawal), `deletion_requested_at` (DateTimeField, nullable — set when participant requests data deletion), `deleted_at` (DateTimeField, nullable — set when staff processes the deletion request, confirms compliance).
- Add `__str__` returning the user's email.
- Create a Django signal (or allauth signal) that auto-creates a `Participant` when a new `User` is created.
- Run `makemigrations` and `migrate`.
- **Verify:** Creating a user in the shell also creates a Participant. Admin shows Participant inline.

### Action 1.2 — Consent Models
**Depends on:** 1.1
**Description:** Create the consent system models.
- `ConsentDocument`: version, title, body (TextField, markdown), is_active, published_at, created_at, updated_at.
- `ConsentRecord`: participant (FK), consent_document (FK), consented (bool), consented_at, ip_address (GenericIPAddressField), user_agent (CharField).
- `OptionalConsentRecord`: participant (FK), consent_type (CharField, choices), consented (bool), consented_at, withdrawn_at (nullable).
- Add `__str__` to all models.
- Register all in Django admin with list_display, list_filter, search_fields.
- Add admin action to export consent records as CSV.
- Run `makemigrations` and `migrate`.
- **Verify:** Can create a ConsentDocument in admin, create a ConsentRecord in the shell, query active consent for a participant.

### Action 1.3 — Unified Survey System Models
**Depends on:** 0.5
**Description:** Create the `SurveyQuestion` and `SurveyResponse` models.
- `SurveyQuestion`: text, help_text, question_type (choices: text/number/single_choice/multi_choice/scale), choices (JSONField, nullable), scale_min, scale_max, min_label, max_label, mid_label, context (choices: profile/post_challenge/post_session), category (nullable), is_required, is_active, display_order, created_at, updated_at.
- `SurveyResponse`: participant (FK), question (FK), value (TextField), answered_at, session (FK, nullable), challenge_attempt (FK, nullable), supersedes (FK self, nullable).
- Add `__str__` to both.
- Add `CheckConstraint`s to `SurveyResponse.Meta.constraints` enforcing context FK rules: profile rows must have both FKs NULL; post_challenge rows must have `challenge_attempt` set and `session` NULL; post_session rows must have `session` set and `challenge_attempt` NULL; both FKs set is always invalid.
- Add `SurveyResponse.clean()` validating the same rules with clear `ValidationError` messages.
- Register in Django admin with filters by context, is_active, question_type.
- Run `makemigrations` and `migrate`.
- Write tests covering all six invalid FK combinations (e.g., profile+session, post_challenge+no attempt, both FKs set) plus the three valid cases.
- **Verify:** Can create questions in admin, create responses in the shell, filter questions by context. Invalid FK combinations are rejected at both DB and model level.

### Action 1.4 — Challenge and Session Models
**Depends on:** 1.1
**Description:** Create the challenge and session models.
- `Challenge`: external_id (CharField, unique — versioned, e.g. `exercism-two-fer-v1`), title, description (TextField, markdown), skeleton_code (TextField), test_cases (JSONField), test_cases_hash (CharField — SHA-256 of test_cases JSON, auto-computed in `save()`), difficulty (IntegerField, 1–5 for tiers), tags (JSONField), is_active (bool), created_at, updated_at. **Never hard-delete or mutate challenges once used** — to fix test cases, deactivate the old challenge and create a new row with a versioned `external_id`. Override `Model.delete()` to raise `ProtectedError` and use `on_delete=PROTECT` on FKs pointing to Challenge.
- `Session`: participant (FK), status (CharField, choices: `in_progress`/`completed`/`abandoned`, default `in_progress`), started_at, completed_at (nullable), abandoned_at (nullable), challenges_attempted (IntegerField, default 0), distraction_free (CharField(max_length=10, choices: "yes"/"mostly"/"no", nullable)), device_type (CharField, choices: "desktop"/"laptop"/"tablet"/"phone", nullable — **self-reported** by participant at session start), pyodide_load_ms (PositiveIntegerField, nullable — Pyodide init time, sent from client), editor_ready (BooleanField, default False — set True once CodeMirror + Pyodide are both initialised, sent from client).
- `SessionChallenge` (join table): session (FK), challenge (FK), position (PositiveIntegerField). `unique_together = (session, challenge)`, `ordering = ["position"]`. This replaces a JSONField to guarantee referential integrity — if a Challenge is referenced by any SessionChallenge or ChallengeAttempt, the DB prevents deletion.
- `ChallengeAttempt`: participant (FK), challenge (FK), session (FK), attempt_uuid (UUIDField, unique — client-generated idempotency key), submitted_code (TextField), tests_passed (IntegerField), tests_total (IntegerField), time_taken_seconds (FloatField), active_time_seconds (FloatField), idle_time_seconds (FloatField), started_at, submitted_at, skipped (BooleanField), think_aloud_active (BooleanField, default False), technical_issues (BooleanField, default False — set if Pyodide crashed/reloaded during this attempt), paste_count (IntegerField, default 0), paste_total_chars (IntegerField, default 0), keystroke_count (IntegerField, default 0), tab_blur_count (IntegerField, default 0). `unique_together = (session, challenge)` — exactly one attempt per challenge per session.
- Add `__str__` to all models.
- Register in Django admin.
- Add indexes on: `ChallengeAttempt.participant`, `ChallengeAttempt.session`, `Challenge.difficulty`, `Challenge.is_active`.
- Add `CheckConstraint` on Session: `completed_at` must be set when `status="completed"`, `abandoned_at` must be set when `status="abandoned"`.
- Run `makemigrations` and `migrate`.
- **Verify:** Can create challenges in admin, create sessions and attempts in the shell. Duplicate `(session, challenge)` attempt is rejected. Duplicate `attempt_uuid` is rejected.

---

## Phase 2: Consent Flow

### Action 2.1 — Consent Gate Middleware / Decorator
**Depends on:** 1.2
**Description:** Implement the consent gate so logged-in users without active consent are redirected to the consent page.
- Create a middleware or view decorator that checks `participant.has_active_consent`. If False, redirect to `/consent/`.
- Exempt: the consent page itself, logout, static files, allauth URLs.
- If the active `ConsentDocument` version is newer than the participant's latest `ConsentRecord`, treat consent as stale (redirect to re-consent).
- **Verify:** New user logs in → redirected to consent page. After consenting → can access the rest of the app. Updating the ConsentDocument version → existing user redirected on next visit.

### Action 2.2 — Consent Page View and Template
**Depends on:** 2.1
**Description:** Build the consent form page.
- View fetches the active `ConsentDocument` and renders its body (markdown → HTML).
- Form: checkbox "I have read and understand the above, and I consent to participate", submit button "Give consent".
- Optional consent checkboxes: reminder emails, think-aloud audio, transcript sharing.
- On POST: create `ConsentRecord` (capture IP, user agent), create `OptionalConsentRecord` entries, set `participant.has_active_consent = True`, redirect to profile intake.
- Decline path: show a message explaining they can return later.
- Style with Bulma.
- **Verify:** Full consent flow works end-to-end. ConsentRecord appears in admin. Declining blocks access. Re-consent flow works after document version update.

---

## Phase 3: Profile Intake

### Action 3.1 — Seed Default Survey Questions
**Depends on:** 1.3
**Description:** Create a data migration or management command that seeds the 24 default profile questions, 3 post-challenge questions, and the post-session habit questions.
- Use `SurveyQuestion` model with correct `context`, `question_type`, `choices`, scales, categories, and display_order.
- Make the command idempotent (skip if questions already exist).
- **Verify:** Run the command. Admin shows all questions with correct contexts and ordering.

### Action 3.2 — Survey Question Renderer (Reusable Component)
**Depends on:** 1.3
**Description:** Build a reusable Django template tag / inclusion tag that renders a `SurveyQuestion` as the appropriate HTML widget.
- Input: a `SurveyQuestion` instance.
- Output: the correct Bulma-styled form widget based on `question_type`:
  - `text` → text input
  - `number` → number input
  - `single_choice` → radio buttons or dropdown
  - `multi_choice` → checkbox group
  - `scale` → horizontal slider or tappable scale with min/mid/max labels
- Include `help_text` display and `is_required` validation.
- Make it accessible: proper `<label>`, `aria-describedby` for help text, keyboard-operable slider.
- **Verify:** Template tag renders each question type correctly. Test with a few sample questions in a throwaway view.

### Action 3.3 — Profile Intake View
**Depends on:** 2.2, 3.1, 3.2
**Description:** Build the intake questionnaire page shown after consent.
- View fetches all active `SurveyQuestion` entries with `context="profile"`, ordered by `display_order`, grouped by `category`.
- Renders them using the reusable question renderer (Action 3.2).
- On POST: validate and create `SurveyResponse` entries for each answer. Set `participant.profile_completed = True`.
- Redirect to the main dashboard / session start page.
- Consider using HTMX for per-category submission (submit one category at a time without full page reload) to allow partial saves naturally.
- **Verify:** New user sees all 24 questions grouped by category. Submitting saves responses. Profile page is accessible again later for edits. Editing creates new `SurveyResponse` with `supersedes` pointing to old one.

### Action 3.4 — Participant Withdrawal and Data Deletion
**Depends on:** 1.1, 1.2, 3.3
**Description:** Build the user-facing withdrawal and data deletion controls on the profile/settings page.
- Add a **"Withdraw from study"** section on the profile page with a clearly labelled button.
- On click: show a confirmation dialog (HTMX partial or JS confirm) explaining: withdrawal prevents future sessions, data is retained in anonymised form unless deletion is requested, they can re-enrol later.
- On confirmation: set `Participant.withdrawn_at = now()`, set `has_active_consent = False`. If a session is in progress, mark it as incomplete.
- After withdrawal, show a **"Request data deletion"** button (only visible once withdrawn).
- On deletion request: set `Participant.deletion_requested_at = now()`. Send a notification to staff (email or admin flag).
- Create a helper function (in `helpers/task_helpers.py`) that processes deletion: deletes `SurveyResponse` rows, blanks `ChallengeAttempt.submitted_code`, deletes `ThinkAloudRecording` files, deletes `OptionalConsentRecord` rows, clears profile fields. Retains anonymised timing/accuracy data and `ConsentRecord` audit log. Sets `Participant.deleted_at = now()` on completion.
- **Admin tooling:** add a Django admin action "Process deletion request" on the Participant list. The action calls the deletion helper, sets `deleted_at`, and logs the admin user who processed it. Add a list filter for "Pending deletion requests" (`deletion_requested_at` set, `deleted_at` null) so staff can easily find outstanding requests.
- Add an admin view or export showing deletion audit trail: participant (opaque ID), `deletion_requested_at`, `deleted_at`, processed by (staff username).
- The consent gate (Action 2.1) must check `withdrawn_at` — withdrawn participants cannot start sessions.
- The export command (Action 7.4) must exclude participants where `withdrawn_at` or `deletion_requested_at` is set.
- **Verify:** Withdrawn participant cannot start new sessions. Deletion request flags the participant. Admin can process deletion via admin action. `deleted_at` is set after processing. Running the deletion helper removes PII but retains anonymised data. Export excludes withdrawn/deleted participants. Audit trail shows who processed the deletion and when.

---

## Phase 4: Challenge Infrastructure

### Action 4.1 — Challenge Data Import
**Depends on:** 1.4
**Description:** Create a management command to import challenges from Exercism and/or APPS dataset.
- Parse Exercism Python track exercises: extract slug, description, test cases, and generate skeleton code (function signature with `pass` body).
- Parse APPS dataset: extract problem statement, test cases, difficulty level. Map APPS difficulty (introductory/interview/competition) to our tiers (3/4/5).
- Assign tier (1–5) and tags.
- Import into `Challenge` model.
- Target: at least 50 challenges for MVP (~15 Tier 1, ~15 Tier 2, ~10 Tier 3, ~5 Tier 4, ~5 Tier 5).
- Make the command idempotent (skip existing by `external_id`).
- **Verify:** Run the command. Admin shows challenges with correct tiers, descriptions, skeleton code, and test cases.

### Action 4.2 — Pyodide Integration (Code Editor Page)
**Depends on:** 0.1
**Description:** Build the in-browser Python execution engine.
- Create a standalone HTML page / Django template that:
  - Loads Pyodide from CDN.
  - Displays a code editor (CodeMirror 6 — accessible, keyboard-navigable).
  - Has a "Run" button that executes the code via Pyodide in a Web Worker.
  - Shows stdout/stderr output below the editor.
- Pre-load Pyodide while user reads instructions (show progress bar).
- Execute test cases client-side: run user code, compare output against expected results, display pass/fail per test.
- Capture timing: start timer on editor display, stop on submit.
- Capture telemetry: paste event listener (count + chars), keystroke counter, tab blur listener.
- Capture idle detection: track tab focus loss >30s and keystroke gaps >2min.
- **Verify:** Can type Python code, run it, see output. Test cases run and show pass/fail. Timing and telemetry values are captured in JS (console.log for now).

### Action 4.3 — Challenge Selection Algorithm
**Depends on:** 1.4
**Description:** Implement the server-side challenge selection logic.
- Given a participant, query all active challenges.
- Exclude challenges the participant has already been shown (via `ChallengeAttempt` records, including skipped).
- Sample randomly per tier distribution: 3 T1, 3 T2, 2 T3, 1 T4, 1 T5. Store this distribution in a `StudyConfig` singleton model (use `django-solo` or a simple model with `objects.get_or_create`): `tier_distribution` (JSONField, e.g. `{"1": 3, "2": 3, "3": 2, "4": 1, "5": 1}`), `embargo_start_date` (DateField, nullable — auto-set on first session completion), and other site-wide study parameters. Register in admin with a clear "Study Configuration" section.
- If a tier is exhausted, fill from adjacent tiers.
- Sort selected challenges by ascending difficulty.
- Return the ordered list of challenge IDs.
- Write as a service function in `challenges/services.py` (not in a view).
- **Verify:** Unit tests: correct tier distribution, no repeats, handles pool exhaustion gracefully, ascending order.

---

## Phase 5: Session Flow

### Action 5.1 — Session Start View
**Depends on:** 2.1, 3.3, 4.3
**Description:** Build the "start session" page and enforce the 28-day rule.
- Check: participant has active consent, profile completed, not withdrawn, and >= 28 days since last **completed** session (status="completed"; abandoned sessions do NOT count).
- **Resumable sessions:** if the participant has an `in_progress` session that's less than 4 hours old, redirect them back to it instead of showing the start page.
- If an `in_progress` session exists but is older than 4 hours, mark it as `abandoned` (set `status="abandoned"`, `abandoned_at=now()`), then proceed as normal.
- If not eligible (28-day rule): show a message explaining when they can next participate (with countdown).
- If eligible: show the session environment guidelines (§4.2) with acknowledgement checkbox and a **"What device are you using?"** radio group (Desktop / Laptop / Tablet / Phone).
- On POST (acknowledged): create a `Session` record with `device_type` from the form. `pyodide_load_ms` and `editor_ready` are updated later by the client via JS callbacks once the editor initialises. Run the challenge selection algorithm (Action 4.3), create `SessionChallenge` rows linking the selected challenges in position order, redirect to the first challenge.
- **Verify:** 28-day enforcement works (test with recent session). Withdrawn participant is blocked. Environment guidelines displayed. Device type saved. Session created with correct `SessionChallenge` entries.

### Action 5.2 — Challenge Attempt View (Single-Page Session with HTMX)
**Depends on:** 4.2, 5.1
**Description:** Build the main session page. The entire session (challenges, reflections, "another?" prompts) lives at **one URL** (e.g. `/sessions/<id>/`). Transitions between states use **HTMX partial swaps** — no full page reloads during a session. The code editor and Pyodide remain in vanilla JS (HTMX doesn't apply there).
- **Session page layout:** a persistent container with the code editor area. HTMX swaps content within a target div for transitions.
- **Challenge display:** challenge description, skeleton code in CodeMirror, visible timer (mm:ss, toggleable), "Submit" and "Skip" buttons, subtle "Stop session" link in corner.
- **On Submit:** JS executes tests via Pyodide (client-side), collects results (tests_passed, tests_total, timing, telemetry), then JS triggers an HTMX POST to the same session URL with the results as form data. Include the client-generated `attempt_uuid` (UUID v4, generated when the challenge is first displayed). Server checks for existing `attempt_uuid` — if found, returns existing result (idempotent). Otherwise creates the `ChallengeAttempt` and returns the reflection questions partial.
- **On Skip:** HTMX POST to the same URL with `skipped=True`. Server creates `ChallengeAttempt` with `skipped=True`, returns the reflection questions partial.
- **On "Stop session":** confirm dialog (JS), then HTMX POST to the same URL with `action=stop`. Server records current challenge as skipped, returns the post-session survey partial.
- The view detects `request.headers.get("HX-Request")` and returns the appropriate partial (`partials/_reflection.html`, `partials/_another_prompt.html`, `partials/_next_challenge.html`, `partials/_post_session_survey.html`) depending on the action and session state.
- **Verify:** Full challenge flow works without page reloads: see challenge → write code → submit → results + reflection questions → another/done. All data saved correctly. Skip and stop-session paths work. Browser back button handled gracefully.

### Action 5.3 — Post-Challenge Reflection Questions (HTMX Partial)
**Depends on:** 3.2, 5.2
**Description:** After each challenge attempt, HTMX swaps in the reflection questions.
- Server returns `partials/_reflection.html` containing active `SurveyQuestion` entries with `context="post_challenge"`, rendered via the reusable question renderer.
- On submit: HTMX POST to the same session URL. Server creates `SurveyResponse` entries linked to the `ChallengeAttempt`, returns `partials/_another_prompt.html`.
- Optional: participant can skip the reflection (HTMX POST with `action=skip_reflection`), goes straight to the "another?" prompt.
- "Another?" prompt: [ Another challenge ] triggers HTMX GET that swaps in the next challenge partial. [ I'm done for today ] triggers HTMX POST that returns the post-session survey partial.
- On 10th challenge: show session-complete message instead of "another?" prompt.
- **Verify:** Reflection questions appear after each attempt via HTMX swap. Responses saved with correct FK. Skipping works. Another/done routing works. No full page reloads.

### Action 5.4 — Post-Session Survey and Session Completion (HTMX Partial)
**Depends on:** 3.2, 5.2
**Description:** Build the post-session habit survey as an HTMX partial.
- Server returns `partials/_post_session_survey.html` containing active `SurveyQuestion` entries with `context="post_session"`, rendered via the reusable question renderer.
- Include the optional distraction question: "Were you able to work without distractions?" (Yes / Mostly / No).
- On submit: HTMX POST to the same session URL. Server creates `SurveyResponse` entries linked to the `Session`. Mark `Session.completed_at`. Update `Session.challenges_attempted`. Return a redirect header (`HX-Redirect`) to the personal results dashboard.
- **Verify:** Post-session survey appears via HTMX swap after ending a session. Responses saved. Session marked complete. Redirects to results page.

---

## Phase 6: Results and Dashboard

### Action 6.1 — Personal Results Page
**Depends on:** 1.4, 5.4
**Description:** Build a basic personal results page for the participant.
- Show a table/list of past sessions: date, challenges attempted, average accuracy, average time.
- Show a simple line chart (Chart.js or Plotly.js) of accuracy over sessions.
- Show a simple line chart of average speed over sessions.
- Use a colourblind-friendly palette. Include text summary below each chart.
- Accessible: charts have `aria-label`, data table alternative available.
- **Caching:** cache per-participant dashboard data for 10 minutes (invalidated on new session completion). Use Django's per-view cache with a key based on `participant.pk` + `participant.profile_updated_at`.
- **Verify:** Participant with 2+ sessions sees charts with data points. Participant with 0 sessions sees an encouraging "complete your first session" message.

### Action 6.2 — Front-Page Landing Page
**Depends on:** 1.4
**Description:** Build the public landing page.
- Hero section: project name, one-line description, "Join the study" CTA button.
- "The Big Question" section: placeholder for aggregate chart (will populate once data exists). For now, show a placeholder with explanation.
- Participation stats: total participants, total sessions, total challenges solved (live from DB, cached).
- Call for Collaborators section (§13.3): description, link to GitHub and collaborator interest form.
- Sponsors section (§13.4): admin-managed `Sponsor` model (name, logo, url, display_order). Render logo grid.
- Footer: links to GitHub, Discord, privacy policy, contact.
- Style with Bulma. Responsive. Accessible.
- **Verify:** Page loads for anonymous users. Stats update when data exists. Sponsor logos render from admin data.

### Action 6.3 — Sponsor Model
**Depends on:** 0.5
**Description:** Create a simple `Sponsor` model for the front page.
- Fields: name, logo (ImageField), url, tier (CharField, optional), display_order, is_active.
- Register in admin.
- **Verify:** Can add sponsors in admin. They render on the landing page in order.

---

## Phase 7: Admin and Data Management

### Action 7.1 — Admin Dashboard
**Depends on:** 1.1, 1.2, 1.3, 1.4
**Description:** Enhance the Django admin for study management.
- Participant admin: show consent status, profile completion, session count, last session date.
- Session admin: list with participant, date, challenges attempted, completion status.
- ChallengeAttempt admin: show participant, challenge, accuracy, time, integrity fields (paste_count etc).
- SurveyQuestion admin: filter by context, is_active. Drag-to-reorder if feasible (django-admin-sortable2), otherwise display_order field.
- ConsentDocument admin: show version, is_active, published_at. Warn if creating a new active version (existing participants will need re-consent).
- Add export-to-CSV actions where relevant (consent records, survey responses, challenge attempts).
- **Permissions and audit logging:**
  - Install `django-simple-history` for audit logging on sensitive models: `ConsentDocument`, `SurveyQuestion`, `Challenge`. This records who changed what and when, critical for research instrument integrity.
  - Define custom permissions: `can_export_data` (for CSV export actions and dataset export), `can_edit_survey_questions`, `can_edit_consent_documents`, `can_process_deletion` (for processing deletion requests).
  - Assign permissions to appropriate groups (e.g. "Researcher" group gets export permissions, "Study Admin" gets all).
  - ConsentDocument and SurveyQuestion should be read-only for non-superusers without the explicit edit permission.
- **Verify:** All admin views load with correct data. Filters work. CSV exports produce valid files. History tab shows changes on ConsentDocument/SurveyQuestion/Challenge. Staff without `can_edit_consent_documents` cannot modify consent text. Deletion processing requires `can_process_deletion`.

### Action 7.2 — Reminder Email System (Huey)
**Depends on:** 1.1, 1.2
**Description:** Implement opt-in monthly reminder emails.
- Create a Huey periodic task that runs daily.
- For each participant where: `has_active_consent=True`, has `OptionalConsentRecord` for `reminder_emails` with `consented=True`, last completed session was > 28 days ago, no reminder sent in the last 28 days.
- Send a simple email: "It's been a while — ready for your next coding session?" with link to the app.
- Log reminder sends in a `ReminderLog` model (participant, sent_at) to avoid duplicate sends.
- Business logic in `helpers/task_helpers.py`, Huey task in `tasks.py` (per guidelines).
- **Verify:** Huey task runs. Eligible participants receive email. Ineligible participants don't. No duplicate sends.

### Action 7.3 — Abandoned Session Cleanup (Huey)
**Depends on:** 1.4
**Description:** Create a Huey periodic task to mark stale sessions as abandoned.
- Runs hourly. Finds all `Session` records where `status="in_progress"` and `started_at` is more than 4 hours ago.
- Sets `status="abandoned"`, `abandoned_at=now()`.
- Business logic in `helpers/task_helpers.py`, Huey task in `tasks.py` (per guidelines).
- **Verify:** Create a session with `started_at` 5 hours ago. Run the task. Session status is now `abandoned`. A session started 1 hour ago is untouched.

### Action 7.4 — PII Retention Cleanup (Huey)
**Depends on:** 1.2, 1.4
**Description:** Create a Huey periodic task that purges retained PII after the 24-month retention period (see §7.5 of plan).
- Runs weekly. Finds `ConsentRecord` rows where `consented_at` is more than 24 months ago and `ip_address` is not null/blank. Sets `ip_address = None`, `user_agent = ""`.
- Session model no longer stores any PII (device type is self-reported, no UA/browser/OS/timezone/screen data), so no session-level cleanup is needed.
- Business logic in `helpers/task_helpers.py`, Huey task in `tasks.py` (per guidelines).
- **Verify:** Create a consent record dated 25 months ago with an IP. Run the task. IP is now null, user_agent is blank. A record from 6 months ago is untouched.

### Action 7.5 — Anonymised Dataset Export Command
**Depends on:** 1.1, 1.2, 1.3, 1.4
**Description:** Build a reproducible, versioned management command for anonymised dataset export (see §12.4 of plan).
- Create management command `export_dataset` in a suitable app (e.g. `dashboard` or a new `exports` app).
- **Anonymisation logic** (in a helper module per guidelines):
  - Map `Participant.pk` → stable opaque ID using `HMAC-SHA256(EXPORT_SECRET_KEY, pk)`. Add `EXPORT_SECRET_KEY` to settings (env var, separate from `SECRET_KEY`).
  - Strip PII fields: email, username, IP address, user agent.
  - Coarsen: age → age band, geography → region/continent, timestamps → date only.
  - Exclude think-aloud transcripts unless participant has `transcript_sharing` optional consent.
  - Exclude withdrawn participants (filter by withdrawal timestamp).
  - Exclude admin/staff users.
- **Export tables** (one CSV + one Parquet per table): Participants (anonymised), Sessions, SessionChallenges, ChallengeAttempts, Challenges, SurveyQuestions, SurveyResponses (with opaque participant ID).
- **Auto-generate `codebook.csv`**: for each exported file, list every column with: file name, column name, data type, description, allowed values (for choice fields).
- **Write `manifest.json`**: dataset version (`vYYYY-MM-DD`), row counts per file, SHA-256 checksum per file, export timestamp, git commit hash (via `subprocess`).
- Output directory: `exports/vYYYY-MM-DD/`. Command accepts `--output-dir` override.
- Add `pyarrow` to dependencies (for Parquet export).
- **Verify:** Running `uv run python manage.py export_dataset` produces a complete export directory. Opaque IDs are stable across re-runs. No PII in exported files — write tests that scan all exported files for: email patterns (`*@*.*`), IPv4 patterns (`\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}`), and raw user agent substrings (`Mozilla/`, `Chrome/`, `Safari/`). Codebook covers all columns. Manifest checksums match file contents.

### Action 7.6 — Dataset Download View and Embargo Enforcement
**Depends on:** 7.5, 1.4
**Description:** Build the gated dataset download view and embargo enforcement.
- Add a site-wide setting `EMBARGO_START_DATE` (DateField). Auto-set on first `Session` completion (use a post-save signal or check in the session completion view). Also editable via admin.
- Create a `DatasetAccessGrant` model: user (FK, nullable — for registered researchers), email (for external requests), granted_by (FK → staff user), granted_at, reason (TextField). Register in admin.
- Create a dataset download page at `/data/` showing: embargo status (active/lifted), embargo start date, expected lift date, available dataset versions (list of `exports/v*/manifest.json`).
- Download links (e.g. `/data/download/v2027-03-15/`) are served via a Django view (not static files):
  - Check user is authenticated.
  - If embargo is active (current date < `EMBARGO_START_DATE + 12 months`): check for a `DatasetAccessGrant` for this user. If no grant, return 403 with a message showing when the embargo lifts.
  - If embargo has lifted (or user has a grant): serve the zipped export directory using `FileResponse` with `Content-Disposition: attachment`.
  - Dataset files are stored outside `STATIC_ROOT` and `MEDIA_ROOT` — not publicly accessible.
- **Post-embargo auto-generation:** add a Huey periodic task that runs on the 1st of each quarter (Jan, Apr, Jul, Oct). It runs the `export_dataset` management command and stores the output in the exports directory. Business logic in `helpers/task_helpers.py`.
- **Verify:** Unauthenticated user gets redirected to login. Authenticated user during embargo sees 403 with lift date. User with `DatasetAccessGrant` can download during embargo. After embargo, any authenticated participant can download. Dataset files are not accessible via direct URL guessing. Quarterly export task runs correctly.

---

## Phase 8: Pyodide and Client-Side Polish

### Action 8.1 — Pyodide Web Worker
**Depends on:** 4.2
**Description:** Move Pyodide execution into a Web Worker for non-blocking UI.
- Create a Web Worker that loads Pyodide and accepts code + test cases via `postMessage`.
- Worker runs code, executes test cases, returns results (pass/fail per test, stdout, stderr, elapsed time).
- Main thread shows a "Running..." spinner while waiting.
- Handle timeout: if code runs for >30 seconds, kill the worker and show a timeout message.
- Handle errors: syntax errors, runtime errors — display clearly to the participant.
- **Verify:** Code execution doesn't freeze the UI. Timeout works. Errors display correctly.

### Action 8.2 — Editor Telemetry
**Depends on:** 4.2
**Description:** Wire up the client-side telemetry capture to the editor.
- Attach event listeners to CodeMirror: `paste` event (count + char length via clipboardData), keystroke count, tab `blur`/`focus` events.
- Track idle: detect tab blur >30s and no keystroke for >2min. Accumulate `idle_time_seconds`.
- Compute `active_time_seconds = time_taken_seconds - idle_time_seconds`.
- On submit: include all telemetry fields in the POST payload.
- **Verify:** Paste a block of code → paste_count and paste_total_chars are correct. Switch tabs → tab_blur_count increments. Idle time accumulates correctly.

---

## Phase 9: Front-Page Aggregate Graphs

### Action 9.1 — Aggregate Data API Endpoints
**Depends on:** 1.4
**Description:** Create JSON API endpoints for front-page charts.
- `/api/stats/summary/` — total participants, sessions, challenges solved.
- `/api/stats/accuracy-over-time/` — average accuracy per month across all participants.
- `/api/stats/accuracy-by-vibe-coding/` — average accuracy over time, split by vibe-coding intensity (low/medium/high based on latest `post_session` vibe_coding_pct response).
- **Exclude staff/superusers** from all aggregate queries (filter `participant__user__is_staff=False, participant__user__is_superuser=False`). Also exclude withdrawn participants. This prevents admin testing from polluting public stats.
- Cache responses (5-minute TTL) using Django's cache framework.
- Only return aggregate data with group sizes >= 10.
- **Verify:** Endpoints return valid JSON. Caching works. Small group sizes are excluded. Staff participant data does not appear in aggregates.

### Action 9.2 — Front-Page Charts
**Depends on:** 6.2, 9.1
**Description:** Wire up the landing page charts to the API.
- Use Chart.js or Plotly.js.
- "The Big Question" chart: accuracy over time for high vs. low vibe-coders (from `/api/stats/accuracy-by-vibe-coding/`).
- Participation stats: live numbers from `/api/stats/summary/`.
- Colourblind-friendly palette. Text summary below each chart. Responsive.
- Graceful fallback when insufficient data: show "We need more participants to show trends — join the study!" message.
- **Verify:** Charts render with test data. Fallback message shows with no data. Accessible: text alternatives present.

---

## Phase 10: Deployment

### Action 10.1 — Dockerise the Application
**Depends on:** all prior actions
**Description:** Create Docker configuration for production deployment.
- `Dockerfile`: Python 3.13, install dependencies, collect static, gunicorn.
- `docker-compose.yml`: Django app, PostgreSQL, Redis (for Huey), Huey worker.
- `.env.example` with all required environment variables.
- Configure static file serving (whitenoise or nginx).
- Configure media file storage (local volume or S3-compatible for audio files later).
- **Verify:** `docker-compose up` starts all services. App is accessible. Migrations run. Huey worker processes tasks.

### Action 10.2 — Rollbar Error Tracking (Production Only)
**Depends on:** 10.1
**Description:** Set up Rollbar for production error tracking.
- Install `django-rollbar`. Add to `pyproject.toml`.
- Configure in `production.py` only: add Rollbar middleware, set `ROLLBAR` settings dict with `access_token` from env var (`ROLLBAR_ACCESS_TOKEN`), environment name, root path.
- Do **not** add Rollbar config to `local.py` — it must not run in local dev.
- Add `ROLLBAR_ACCESS_TOKEN` to `.env.example`.
- **Verify:** In production settings, Rollbar middleware is present. In local settings, it is not. Triggering a test error in production sends it to the Rollbar dashboard.

### Action 10.3 — Structured Logging, Metrics, and Backups
**Depends on:** 10.1
**Description:** Set up production observability and backup strategy.
- **Structured logging:**
  - Install `python-json-logger`. Configure Django's `LOGGING` in `production.py` to output JSON-formatted logs.
  - `local.py` uses standard console logging (human-readable).
  - Log key events at INFO level: session start/complete/abandon, challenge attempt submit, consent given/withdrawn, deletion processed, export run, reminder sent.
- **Key metrics model:**
  - Create a simple `MetricEvent` model (or use Django's cache-based counters): event_type (CharField), count (IntegerField), recorded_at (DateField). Track: sessions started/completed/abandoned per day, attempts submitted, Pyodide load failures (reported from client via a lightweight POST endpoint), export runs, reminder emails sent, deletion requests processed.
  - Add an admin dashboard widget or simple admin list view showing daily/weekly counts.
- **Email backend:**
  - `local.py`: `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` (prints to terminal).
  - `production.py`: SMTP or transactional service (Mailgun/Postmark) via env vars (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`).
  - Add all email env vars to `.env.example`.
- **Database backups:**
  - Configure automated daily PostgreSQL backups via Appliku's managed backup feature (or a cron script running `pg_dump` to S3-compatible object storage).
  - Document restore procedure in a `docs/backup-restore.md`.
  - Schedule quarterly restore test (manual — add to project README as an ops checklist item).
- **Verify:** Production logs are JSON-formatted. Metrics increment on key events. Email sends work (test with a reminder trigger). Backup runs and produces a valid dump.

### Action 10.4 — Appliku / Hetzner Deployment
**Depends on:** 10.1, 10.2, 10.3
**Description:** Deploy to Hetzner via Appliku.
- Configure Appliku project pointing to the repo.
- Set environment variables in Appliku dashboard.
- Configure PostgreSQL (Appliku managed or Hetzner-hosted).
- Set up SSL certificate.
- Configure DNS.
- Set up allauth social providers (Google, GitHub) with production redirect URIs.
- **Verify:** App is live at the production URL. Registration, consent, session flow all work. Social login works. Logs are shipping. Rollbar is receiving errors. Backups are running.

---

## Phase 11: Final MVP Polish

### Action 11.1 — Accessibility Audit
**Depends on:** all UI actions
**Description:** Audit all pages against WCAG 2.1 AA.
- Run automated tools (axe-core, Lighthouse accessibility audit) on every page.
- Manual checks: keyboard navigation through entire session flow, screen reader testing, colour contrast verification.
- Fix any issues found.
- **Verify:** Lighthouse accessibility score >= 90 on all pages. Full session flow completable via keyboard only.

### Action 11.2 — End-to-End Smoke Test
**Depends on:** all prior actions
**Description:** Walk through the complete user journey and verify.
- Register new account → consent → intake questionnaire → start session → complete 3 challenges with reflection questions → stop session → post-session survey → view results → log out → log back in → verify 28-day enforcement.
- Check admin: all records created correctly (participant, consent, survey responses, session, challenge attempts).
- Check front page: stats update.
- **Verify:** Zero errors in the full flow. All data persists correctly.

### Action 11.3 — Seed Data for Demo / Testing
**Depends on:** all models
**Description:** Create a management command that generates realistic fake data for testing and demos.
- Create 20 fake participants with varied profiles.
- Each participant has 1–5 sessions with 3–10 challenge attempts each.
- Vary accuracy and timing realistically by tier.
- Include varied vibe-coding percentages in survey responses.
- **Verify:** Running the command populates the database. Charts on the front page and personal dashboards render with realistic-looking data.
