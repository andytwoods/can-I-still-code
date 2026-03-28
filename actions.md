get# Actions: Implementation Breakdown

Each action is a self-contained chunk suitable for an agentic LLM to complete in one session. Actions are ordered by dependency  –  later actions build on earlier ones. Each action specifies what to build, what it depends on, and how to verify it works.

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
| `django-simple-history` | Django admin log is append-only, no field diffs | Consent documents and survey questions are research instruments  –  auditable change history is an ethics requirement. |
| `django-recaptcha` / `django-turnstile` | No built-in CAPTCHA | Registration-only. Lightweight bot friction for a public-facing study. |
| `markdown` | No built-in markdown rendering | Consent docs and challenge descriptions are admin-authored markdown. `markdown` converts to HTML; output is marked `|safe` in templates (admin-trusted content). |
| `pyarrow` | No built-in Parquet support | Dataset export to Parquet for research reproducibility. |
| `whitenoise` | Django's static serving is dev-only | Production static file serving with compressed, cache-busted (hashed) filenames. Needed for stable CSP `'self'` paths. Avoids separate nginx config. |
| `python-json-logger` | Django's logging is plain text | Structured JSON logs are needed for production log aggregation. |

**Django built-ins used where sufficient:** caching (cache framework), permissions/groups, logging (configured via `LOGGING` dict), sessions, CSRF, ORM constraints, admin, signals.

---

## Phase 0: Project Scaffolding

### Action 0.1  –  Django Project Setup ✅
**Depends on:** nothing
**Description:** Initialise the Django project with environment-based settings and core dependencies.
- Run `django-admin startproject config .` (or equivalent).
- Configure `settings.py`: split into `base.py`, `local.py`, `production.py`. Use env vars for `SECRET_KEY`, `DATABASE_URL`, `DEBUG`, `ALLOWED_HOSTS`.
- Set `LANGUAGE_CODE = "en-gb"` and `USE_I18N = False` in `base.py`. The app is **English-only**  –  no internationalisation, no translation infrastructure, no `{% trans %}` tags. All UI text is plain English strings in templates.
- **Database config (per guidelines):**
  – `base.py`: no database defined (or a minimal default that `local.py`/`production.py` override).
  – `local.py`: **SQLite** (`db.sqlite3`)  –  no PostgreSQL dependency for local dev.
  – `production.py`: **PostgreSQL** via `DATABASE_URL` env var, using `dj-database-url` or `django-environ`.
  – Note: Django's `JSONField` and `CheckConstraint` work on both SQLite (3.38+) and PostgreSQL, so the split is safe.
- **Pages app + base template architecture:**
  – Create the `pages` app.
  – Create `pages/templates/base.html` with: Bulma CSS (via CDN), htmx (via CDN), skip-to-content link, semantic HTML structure (`<nav>`, `<main>`, `<footer>`), `{% block content %}`, CSRF token, `{% block extra_js %}`.
  – Create `pages/templates/pages/navbar.html` (included in base): responsive Bulma navbar with login/logout links, user display name. Include a placeholder `{% block hijack_banner %}` for the hijack warning bar (populated in Action 0.4).
  – Create `pages/templates/pages/footer.html` (included in base).
  – Create `pages/templates/pages/messages.html`  –  Django messages display using Bulma notification classes.
  – All other apps extend `base.html` (per guidelines).
- Add a simple health-check view at `/` that renders "Hello world" to confirm everything works.
- **Verify:** `uv run python manage.py runserver` starts, `/` returns 200, `uv run python manage.py migrate` runs cleanly on SQLite. Navbar renders. Messages display.

### Action 0.2  –  Dependency and Tooling Baseline (uv) ✅
**Depends on:** nothing (can run in parallel with 0.1)
**Description:** Establish the dependency management, quality gates, and development workflow using `uv`.
- Define all dependencies in `pyproject.toml` (not `requirements.txt`). Core deps: Django, django-allauth, django-huey, django-crispy-forms, crispy-bulma, django-environ (or python-dotenv), pyarrow. Dev deps: ruff, mypy, pytest, pytest-django, django-stubs.
- Add `psycopg2-binary` as a production-only dependency (not needed for local SQLite dev).
- Configure Ruff in `pyproject.toml`:
  – Enable rules: `E`, `F`, `W`, `I` (isort), `UP` (pyupgrade), `B` (bugbear), `S` (bandit subset), `SIM`.
  – **Enforce no catch-all exceptions** (per guidelines): enable `E722` (bare `except:`), `BLE001` (`except Exception:`). Set both as errors, not warnings.
  – Line length: 120 chars.
  – Target Python 3.13 (matches the project runtime).
- Configure mypy in `pyproject.toml`: strict mode, django-stubs plugin.
- Configure pytest in `pyproject.toml`: `DJANGO_SETTINGS_MODULE = "config.settings.local"`.
- Add a `Makefile` or `scripts` section in `pyproject.toml` with common commands:
  – `uv run python manage.py <command>` for Django management
  – `uv run ruff check .` for linting
  – `uv run pytest` for tests
- **Verify:** `uv sync` installs all deps. `uv run ruff check .` passes on the empty project. `uv run pytest` discovers and runs (zero tests is OK). A deliberate bare `except:` triggers a Ruff error.

### Action 0.3  –  Authentication (django-allauth) ✅
**Depends on:** 0.1, 0.2
**Description:** Set up django-allauth with Google and GitHub social login, plus email/password fallback.
- Install and configure django-allauth in settings (add to `INSTALLED_APPS`, `AUTHENTICATION_BACKENDS`, `MIDDLEWARE`).
- Configure allauth to require email verification (`ACCOUNT_EMAIL_VERIFICATION = "mandatory"`).
- Add Google and GitHub as social providers in settings. Use env vars for client IDs / secrets.
- Create allauth URL includes in `urls.py`.
- Override allauth templates to use Bulma styling and extend `base.html`.
- **Verify:** Registration, login, logout work via email/password. Social login config is present (full testing requires provider credentials). Email verification flow works (can use console email backend for local dev).

### Action 0.4  –  Admin Impersonation (django-hijack) ✅
**Depends on:** 0.3
**Description:** Set up django-hijack so admins can impersonate any user for debugging and support.
- Install `django-hijack`. Add to `INSTALLED_APPS` and `MIDDLEWARE`.
- Configure permissions: only superusers and staff with explicit `hijack` permission can impersonate.
- Enable the admin integration: add a "Hijack" button on the user list and user detail pages in Django admin.
- Add the hijack notification banner to `pages/templates/base.html`  –  a visible warning bar (e.g. bright yellow) shown during hijacked sessions so it's never mistaken for a real user session. Include the "Release" button to end impersonation.
- Configure hijack URL includes in `urls.py`.
- **Verify:** Superuser can hijack a regular user from the admin. Banner appears during hijacked session. "Release" returns to admin. Non-superuser staff without permission cannot hijack.

### Action 0.5  –  Django App Structure ✅
**Depends on:** 0.1
**Description:** Create the Django apps that will house the models. Keep apps focused and minimal.
- `accounts`  –  Participant model, profile views.
- `consent`  –  ConsentDocument, ConsentRecord, OptionalConsentRecord.
- `surveys`  –  SurveyQuestion, SurveyResponse (the unified question system).
- `challenges`  –  Challenge, ChallengeAttempt, session logic.
- `sessions`  –  CodeSession model, session orchestration views.
- `dashboard`  –  Personal results, front-page aggregate views.
- `pages`  –  Static/semi-static pages (landing, about, sponsors, contact, get-involved).
- Register all apps in `INSTALLED_APPS`.
- **Verify:** `uv run python manage.py check` passes. No models yet  –  just the app directories and empty files.

### Action 0.6  –  Security Baseline (CSP, Rate Limiting, Markdown Sanitisation) ✅
**Depends on:** 0.1
**Description:** Set up security infrastructure that affects template structure and middleware early.
- **Content Security Policy (CSP):**
  – Install `django-csp`. Configure in `base.py`.
  – `script-src`: `'self'`, Pyodide CDN origin, chart library CDN origin (Chart.js or Plotly.js). **No `'unsafe-inline'`**.
  – `worker-src`: `'self'`, `blob:` (Pyodide Web Worker).
  – `connect-src`: `'self'` (for HTMX and API fetches).
  – `style-src`: `'self'`, Bulma CDN origin, `'unsafe-inline'` (Bulma requires this for some utilities).
  – `img-src`: `'self'`, `data:` (for chart exports).
  – Document CSP origins in a comment block in settings so future CDN changes are easy.
  – **JS architecture rule (enforced by CSP):** All JavaScript lives in static files under `<app>/static/<app>/js/`. No `<script>` tags in templates or partials  –  HTMX behaviour uses `hx-*` attributes only (these are HTML attributes, not inline JS, so CSP is not affected). For the small amount of page-specific initialisation (e.g. Pyodide setup, chart rendering), use `<script src="{% static '...' %}">` in `{% block extra_js %}`. If a truly unavoidable inline script is needed, use `{% csp_nonce %}`  –  but treat this as an exception that requires justification, not a default pattern.
- **Rate limiting:**
  – Install `django-ratelimit`.
  – Apply rate limits to abuse-prone endpoints: allauth login/register (5/minute per IP), consent POST (10/minute per user), session start (3/minute per user), attempt submission (10/minute per user).
  – Return `429 Too Many Requests` with a Bulma-styled error page.
- **Markdown rendering:**
  – Install `markdown`.
  – Create a template filter `|render_markdown` that converts markdown to HTML via the `markdown` library.
  – Use this filter for: consent document bodies, challenge descriptions, survey question help text.
  – Admin-authored content is trusted  –  use `|safe` after `|render_markdown` in templates. No sanitisation layer needed.
- **Bot friction:**
  – Install `django-recaptcha` (or `django-turnstile` for Cloudflare Turnstile). Configure with env vars.
  – Add CAPTCHA to the registration form only (not login  –  allauth's email verification handles most abuse). Can be made conditional (only shown after N failed attempts) in a later iteration.
- **Static file serving (Whitenoise):**
  – Install `whitenoise`. Add `WhiteNoiseMiddleware` to `MIDDLEWARE` (immediately after `SecurityMiddleware`).
  – Configure `STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"` in `base.py`.
  – This ensures static file paths are stable and cache-busted (hashed filenames), CSP `'self'` works reliably for static JS/CSS, and no separate nginx config is needed for static files.
  – Add `whitenoise` to `pyproject.toml` dependencies.
- **Baseline security headers (Django built-ins):**
  – In `base.py`: `SECURE_CONTENT_TYPE_NOSNIFF = True` (X-Content-Type-Options: nosniff), `X_FRAME_OPTIONS = "DENY"`, `SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"`.
  – In `production.py` only: `SECURE_SSL_REDIRECT = True`, `SECURE_HSTS_SECONDS = 31536000` (1 year), `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`, `SECURE_HSTS_PRELOAD = True`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`.
  – In `local.py`: leave HSTS/SSL settings off (plain HTTP for local dev).
- **Verify:** CSP headers are present in responses. Inline script without nonce is blocked by CSP. Rate-limited endpoint returns 429 after threshold. CAPTCHA renders on registration. `X-Content-Type-Options: nosniff` header present. Static files served with hashed filenames. In production settings, HSTS and SSL redirect are enabled.

---

## Phase 1: Core Models

### Action 1.1  –  Participant Model ✅
**Depends on:** 0.3, 0.5
**Description:** Create the `Participant` model linked to Django's `User`.
- Fields: `user` (OneToOneField → User), `has_active_consent` (BooleanField, default False), `profile_completed` (BooleanField, default False), `profile_updated_at` (DateTimeField, nullable), `withdrawn_at` (DateTimeField, nullable  –  set on withdrawal), `deletion_requested_at` (DateTimeField, nullable  –  set when participant requests data deletion), `deleted_at` (DateTimeField, nullable  –  set when staff processes the deletion request, confirms compliance).
- Add `__str__` returning the user's email.
- Create a Django signal (or allauth signal) that auto-creates a `Participant` when a new `User` is created.
- Run `makemigrations` and `migrate`.
- **Verify:** Creating a user in the shell also creates a Participant. Admin shows Participant inline.

### Action 1.2  –  Consent Models ✅
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

### Action 1.3  –  Unified Survey System Models ✅
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

### Action 1.4  –  Challenge and CodeSession Models ✅
**Depends on:** 1.1
**Description:** Create the challenge and session models.
- `Challenge`: external_id (CharField, unique  –  versioned, e.g. `exercism-two-fer-v1`), title, description (TextField, markdown), skeleton_code (TextField), test_cases (JSONField), test_cases_hash (CharField  –  SHA-256 of test_cases JSON, auto-computed in `save()`), difficulty (IntegerField, 1–5 for tiers), tags (JSONField), is_active (bool), created_at, updated_at. **Never hard-delete or mutate challenges once used**  –  to fix test cases, deactivate the old challenge and create a new row with a versioned `external_id`. Override `Model.delete()` to raise `ProtectedError` and use `on_delete=PROTECT` on FKs pointing to Challenge.
- `CodeSession`: participant (FK), status (CharField, choices: `in_progress`/`completed`/`abandoned`, default `in_progress`), started_at, completed_at (nullable), abandoned_at (nullable), challenges_attempted (IntegerField, default 0), distraction_free (CharField(max_length=10, choices: "yes"/"mostly"/"no", nullable)), device_type (CharField, choices: "desktop"/"laptop"/"tablet"/"phone", nullable  –  **self-reported** by participant at session start), pyodide_load_ms (PositiveIntegerField, nullable  –  Pyodide init time, sent from client), editor_ready (BooleanField, default False  –  set True once CodeMirror + Pyodide are both initialised, sent from client).
- `CodeSessionChallenge` (join table): session (FK), challenge (FK), position (PositiveIntegerField). `unique_together = (session, challenge)`, `ordering = ["position"]`. This replaces a JSONField to guarantee referential integrity  –  if a Challenge is referenced by any CodeSessionChallenge or ChallengeAttempt, the DB prevents deletion.
- `ChallengeAttempt`: participant (FK), challenge (FK), session (FK), attempt_uuid (UUIDField, unique  –  client-generated idempotency key), submitted_code (TextField), tests_passed (IntegerField), tests_total (IntegerField), time_taken_seconds (FloatField), active_time_seconds (FloatField), idle_time_seconds (FloatField), started_at, submitted_at, skipped (BooleanField), think_aloud_active (BooleanField, default False), technical_issues (BooleanField, default False  –  set if Pyodide crashed/reloaded during this attempt), paste_count (IntegerField, default 0), paste_total_chars (IntegerField, default 0), keystroke_count (IntegerField, default 0), tab_blur_count (IntegerField, default 0). `unique_together = (session, challenge)`  –  exactly one attempt per challenge per session.
- Add `__str__` to all models.
- Register in Django admin.
- Add indexes on: `ChallengeAttempt.participant`, `ChallengeAttempt.session`, `Challenge.difficulty`, `Challenge.is_active`.
- Add `CheckConstraint` on CodeSession: `completed_at` must be set when `status="completed"`, `abandoned_at` must be set when `status="abandoned"`.
- Add `CheckConstraint`s on ChallengeAttempt for reasonable value ranges: `time_taken_seconds >= 0`, `active_time_seconds >= 0`, `idle_time_seconds >= 0`, `tests_passed >= 0`, `tests_passed <= tests_total`, `paste_count >= 0`, `keystroke_count >= 0`, `tab_blur_count >= 0`. Add `Model.clean()` for the same rules with clear error messages.
- Add `CheckConstraint` on Challenge: `difficulty >= 1 AND difficulty <= 5`.
- **Cross-model integrity constraints on ChallengeAttempt:**
  – **Participant consistency:** add a `CheckConstraint` (or `Model.clean()` + DB trigger if the ORM can't express the cross-table check) ensuring `ChallengeAttempt.participant == ChallengeAttempt.session.participant`. Since Django `CheckConstraint` cannot reference joined tables, enforce this in `ChallengeAttempt.clean()` and in the submission service function. Write tests that a ChallengeAttempt with a mismatched participant is rejected.
  – **Challenge assignment validation:** the submission service function must verify that `ChallengeAttempt.challenge` is one of the `CodeSessionChallenge` rows for that session (i.e., `CodeSessionChallenge.objects.filter(session=session, challenge=challenge).exists()`). Reject with a clear error if the challenge was not assigned to this session. Write tests for both valid and unassigned challenge submissions.
  – **Position ordering enforcement:** the submission service function must enforce that attempts are submitted in position order  –  only the next unattempted position in the `CodeSessionChallenge` sequence can be submitted (or skipped). This prevents users from skipping ahead or posting out-of-order results by crafting manual POSTs. Write tests: submitting for position 3 when position 2 is unattempted is rejected; submitting for position 2 after position 1 is accepted.
- Run `makemigrations` and `migrate`.
- **Verify:** Can create challenges in admin, create sessions and attempts in the shell. Duplicate `(session, challenge)` attempt is rejected. Duplicate `attempt_uuid` is rejected. Negative timing values are rejected at DB level. Cross-user attempt is rejected. Unassigned challenge attempt is rejected. Out-of-order submission is rejected.

### Action 1.5  –  Study Settings (settings dict) ✅
**Depends on:** nothing
**Description:** Define study parameters as a plain dict in `base.py`. No model, no migration, no caching  –  change the value and restart.
```python
STUDY = {
    "TIER_DISTRIBUTION": {"1": 3, "2": 3, "3": 2, "4": 1, "5": 1},
    "CHALLENGES_PER_SESSION": 10,
    "SESSION_COOLDOWN_DAYS": 28,
    "SESSION_TIMEOUT_HOURS": 4,
    "MIN_GROUP_SIZE_FOR_AGGREGATES": 10,
}
```
- Access everywhere via `from django.conf import settings; settings.STUDY["TIER_DISTRIBUTION"]`.
- **Validation:** add a Django system check (`register` a check function in `apps.py`) that runs on startup and verifies: tier keys are `"1"`–`"5"`, values are non-negative ints summing to `CHALLENGES_PER_SESSION`, cooldown ≥ 1, timeout ≥ 1. Fails `manage.py check` with a clear error if invalid.
- **Embargo start date:** not stored in settings  –  derived at query time as `CodeSession.objects.filter(status="completed").order_by("completed_at").values_list("completed_at", flat=True).first()`. Only checked on the dataset download page (cheap query, one row).
- **Verify:** `uv run python manage.py check` passes. Deliberately invalid tier distribution (wrong sum) fails the check with a clear message.

### Action 1.6  –  Audit Event Model ✅
**Depends on:** 0.5
**Description:** Create a lightweight, append-only audit trail for user-facing critical events. This complements `django-simple-history` (which tracks research instrument changes) by recording **what happened to whom and when** for debugging and ethics reporting.
- `AuditEvent`: `event_type` (CharField, choices  –  see below), `participant` (FK, nullable  –  null for system events like export runs), `actor` (FK → User, nullable  –  the user who triggered the event; null for automated tasks), `timestamp` (DateTimeField, auto_now_add), `metadata` (JSONField, default dict  –  event-specific details, e.g. consent document version, session ID, export path).
- **Event types:** `consent_given`, `consent_withdrawn`, `optional_consent_given`, `optional_consent_withdrawn`, `deletion_requested`, `deletion_processed`, `session_started`, `session_completed`, `session_abandoned`, `dataset_export_run`, `withdrawal`.
- **Append-only:** override `save()` to reject updates on existing rows (raise `ValueError` if `self.pk` is set). Override `delete()` to raise `ProtectedError`. No `update` or `delete` admin actions.
- **Helper function:** `log_audit_event(event_type, participant=None, actor=None, **metadata)`  –  a one-liner callsite for all code that needs to record an event. Import and call from consent views, withdrawal flow, deletion processing, session views, and export command.
- **Admin:** register as read-only (`has_change_permission = False`, `has_delete_permission = False`). List display: timestamp, event_type, participant, actor. Filters: event_type, date range. Search: participant email. Export-to-CSV action for ethics board reporting.
- Run `makemigrations` and `migrate`.
- **Verify:** Creating an event via `log_audit_event()` works. Attempting to update or delete an event raises an error. Admin shows events read-only with filters. CSV export produces valid output.

---

## Phase 2: Consent Flow

### Action 2.1  –  Consent Gate Middleware / Decorator ✅
**Depends on:** 1.2
**Description:** Implement the consent gate so logged-in users without active consent are redirected to the consent page.
- Create a middleware or view decorator that checks `participant.has_active_consent`. If False, redirect to `/consent/`.
- Exempt: the consent page itself, logout, static files, allauth URLs.
- If the active `ConsentDocument` version is newer than the participant's latest `ConsentRecord`, treat consent as stale (redirect to re-consent).
- **Verify:** New user logs in → redirected to consent page. After consenting → can access the rest of the app. Updating the ConsentDocument version → existing user redirected on next visit.

### Action 2.2  –  Consent Page View and Template ✅
**Depends on:** 2.1
**Description:** Build the consent form page.
- View fetches the active `ConsentDocument` and renders its body (markdown → HTML).
- Form: checkbox "I have read and understand the above, and I consent to participate", submit button "Give consent".
- Optional consent checkboxes: reminder emails, think-aloud audio, transcript sharing.
- On POST: create `ConsentRecord` (capture IP, user agent), create `OptionalConsentRecord` entries, set `participant.has_active_consent = True`, call `log_audit_event("consent_given", participant, actor=request.user, consent_document_version=doc.version)`. For each optional consent, call `log_audit_event("optional_consent_given", ...)`. Redirect to profile intake.
- Decline path: show a message explaining they can return later.
- Style with Bulma.
- **Depends also on:** 1.6 (AuditEvent model).
- **Verify:** Full consent flow works end-to-end. ConsentRecord appears in admin. AuditEvent for `consent_given` is created. Declining blocks access. Re-consent flow works after document version update.

---

## Phase 3: Profile Intake

### Action 3.1  –  Seed Default Survey Questions ✅
**Depends on:** 1.3
**Description:** Create a data migration or management command that seeds the 24 default profile questions, 3 post-challenge questions, and the post-session habit questions.
- Use `SurveyQuestion` model with correct `context`, `question_type`, `choices`, scales, categories, and display_order.
- Make the command idempotent (skip if questions already exist).
- **Verify:** Run the command. Admin shows all questions with correct contexts and ordering.

### Action 3.2  –  Dynamic Survey Form Builder ✅
**Depends on:** 1.3, 0.2
**Description:** Create a helper function that dynamically builds a Django `Form` class from a queryset of `SurveyQuestion` objects. Rendered via crispy-forms + crispy-bulma (per guidelines).
- Create `surveys/forms.py` with a `build_survey_form(questions_qs)` function that returns a `Form` class. Field mapping:
  – `text` → `forms.CharField(widget=forms.TextInput)`
  – `number` → `forms.IntegerField`
  – `single_choice` → `forms.ChoiceField(widget=forms.RadioSelect, choices=q.choices)`
  – `multi_choice` → `forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=q.choices)`
  – `scale` → `forms.IntegerField(min_value=q.scale_min, max_value=q.scale_max)` with a range widget showing min/mid/max labels
- Each field's `label` is set from `q.text`, `help_text` from `q.help_text`, `required` from `q.is_required`.
- Field names use `question_{q.pk}` so the view can map answers back to questions.
- Render in templates with `{% load crispy_forms_tags %}` and `{% crispy form %}`  –  crispy-bulma handles all Bulma styling.
- Accessible: crispy-forms generates proper `<label>` and `aria-describedby` for help text. Scale widget needs a custom crispy layout or widget override to show min/mid/max labels.
- **Verify:** Build a form from a queryset containing one of each question type. Render it in a throwaway view  –  all five types display with correct Bulma styling. Submit with invalid data  –  Django validation catches it. Submit with valid data  –  `form.cleaned_data` contains the right types.

### Action 3.3  –  Profile Intake View (HTMX Per-Category Steps) ✅
**Depends on:** 2.2, 3.1, 3.2
**Description:** Build the intake questionnaire as a multi-step HTMX flow, one category at a time.
- **Same-endpoint pattern (per guidelines):** a single URL `/profile/intake/`. The view groups active `SurveyQuestion` entries with `context="profile"` by `category`, ordered by `display_order`.
- On initial GET: render the first category's questions in a partial, with a progress indicator ("Step 1 of 5  –  Demographics").
- On POST (HTMX): validate and save `SurveyResponse` entries for that category. Return the next category's partial via HTMX swap. Each category is persisted immediately  –  if the user closes the tab mid-flow, completed categories are saved.
- On final category POST: set `participant.profile_completed = True`, return an `HX-Redirect` to the dashboard / session start page.
- If the user returns to `/profile/intake/` later (for edits), show the first category pre-filled with existing responses. On submit, create new `SurveyResponse` rows with `supersedes` pointing to the old ones.
- **Post-challenge and post-session questions** (2–5 questions each) are already rendered as HTMX partials within the session page  –  they are short enough to show all at once within their partial, no per-question stepping needed.
- **Verify:** Intake flow steps through each category via HTMX swaps. Each step saves immediately. Progress indicator updates. Closing mid-flow preserves completed categories. Re-visiting pre-fills answers. Editing creates superseding responses.

### Action 3.4  –  Participant Withdrawal and Data Deletion ✅
**Depends on:** 1.1, 1.2, 1.6, 3.3
**Description:** Build the user-facing withdrawal and data deletion controls on the profile/settings page.
- Add a **"Withdraw from study"** section on the profile page with a clearly labelled button.
- On click: show a confirmation dialog (HTMX partial or JS confirm) explaining: withdrawal prevents future sessions, data is retained in anonymised form unless deletion is requested, they can re-enrol later.
- On confirmation: set `Participant.withdrawn_at = now()`, set `has_active_consent = False`. If a session is in progress, mark it as incomplete. Call `log_audit_event("withdrawal", participant, actor=request.user)`.
- After withdrawal, show a **"Request data deletion"** button (only visible once withdrawn).
- On deletion request: set `Participant.deletion_requested_at = now()`. Send a notification to staff (email or admin flag). Call `log_audit_event("deletion_requested", participant, actor=request.user)`.
- Create a helper function (in `helpers/task_helpers.py`) that processes deletion: deletes `SurveyResponse` rows, blanks `ChallengeAttempt.submitted_code`, deletes `ThinkAloudRecording` files, deletes `OptionalConsentRecord` rows, clears profile fields. Retains anonymised timing/accuracy data and `ConsentRecord` audit log. Sets `Participant.deleted_at = now()` on completion.
- **Admin tooling:** add a Django admin action "Process deletion request" on the Participant list. The action calls the deletion helper, sets `deleted_at`, calls `log_audit_event("deletion_processed", participant, actor=request.user)`, and logs the admin user who processed it. Add a list filter for "Pending deletion requests" (`deletion_requested_at` set, `deleted_at` null) so staff can easily find outstanding requests.
- Add an admin view or export showing deletion audit trail: participant (opaque ID), `deletion_requested_at`, `deleted_at`, processed by (staff username).
- The consent gate (Action 2.1) must check `withdrawn_at`  –  withdrawn participants cannot start sessions.
- The export command (Action 7.4) must exclude participants where `withdrawn_at` or `deletion_requested_at` is set.
- **Verify:** Withdrawn participant cannot start new sessions. Deletion request flags the participant. Admin can process deletion via admin action. `deleted_at` is set after processing. Running the deletion helper removes PII but retains anonymised data. Export excludes withdrawn/deleted participants. Audit trail shows who processed the deletion and when.

---

## Phase 4: Challenge Infrastructure

### Action 4.1  –  Challenge Data Import ✅
**Depends on:** 1.4
**Description:** Create a management command to import challenges from Exercism and/or APPS dataset.
- Parse Exercism Python track exercises: extract slug, description, test cases, and generate skeleton code (function signature with `pass` body).
- Parse APPS dataset: extract problem statement, test cases, difficulty level. Map APPS difficulty (introductory/interview/competition) to our tiers (3/4/5).
- Assign tier (1–5) and tags.
- Import into `Challenge` model.
- Target: at least 50 challenges for MVP (~15 Tier 1, ~15 Tier 2, ~10 Tier 3, ~5 Tier 4, ~5 Tier 5).
- Make the command idempotent (skip existing by `external_id`).
- **Verify:** Run the command. Admin shows challenges with correct tiers, descriptions, skeleton code, and test cases.

### Action 4.2  –  Pyodide Integration (Code Editor Page) ✅
**Depends on:** 0.1
**Description:** Build the in-browser Python execution engine.
- Create a standalone HTML page / Django template that:
  – Loads Pyodide from CDN.
  – Displays a code editor (CodeMirror 6  –  accessible, keyboard-navigable).
  – Has a "Run" button that executes the code via Pyodide in a Web Worker.
  – Shows stdout/stderr output below the editor.
- Pre-load Pyodide while user reads instructions (show progress bar).
- Execute test cases client-side: run user code, compare output against expected results, display pass/fail per test.
- Capture timing: start timer on editor display, stop on submit.
- Capture telemetry: paste event listener (count + chars), keystroke counter, tab blur listener.
- Capture idle detection: track tab focus loss >30s and keystroke gaps >2min.
- **Verify:** Can type Python code, run it, see output. Test cases run and show pass/fail. Timing and telemetry values are captured in JS (console.log for now).

### Action 4.3  –  Challenge Selection Algorithm ✅
**Depends on:** 1.4, 1.5
**Description:** Implement the server-side challenge selection logic.
- Given a participant, query all active challenges.
- Exclude challenges the participant has already been shown (via `ChallengeAttempt` records, including skipped).
- Read the tier distribution and `challenges_per_session` from `settings.STUDY` (Action 1.5).
- If a tier is exhausted, fill from adjacent tiers.
- **Pool exhaustion handling:** if fewer than 10 challenges remain for a participant across all tiers, show a message: *"You've completed most of our challenges! We're adding new ones regularly."* If zero challenges remain, prevent session start with a friendly explanation.
- **Admin alert:** log a warning (and optionally send a staff email) when any participant's remaining pool drops below 20 challenges, so admins know to add more content.
- Sort selected challenges by ascending difficulty.
- Return the ordered list of challenge IDs.
- Write as a service function in `challenges/services.py` (not in a view).
- **Verify:** Unit tests: correct tier distribution, no repeats, handles pool exhaustion gracefully, ascending order. Near-exhaustion warning triggers. Zero-pool blocks session start.

---

## Phase 5: Session Flow

### Action 5.1  –  Session Start View ✅
**Depends on:** 2.1, 3.3, 4.3
**Description:** Build the "start session" page and enforce the 28-day rule.
- Check: participant has active consent, profile completed, not withdrawn, and >= 28 days since last **completed** session (status="completed"; abandoned sessions do NOT count).
- **Resumable sessions:** if the participant has an `in_progress` session that's less than 4 hours old, redirect them back to it instead of showing the start page  –  **regardless of device/browser**. One participant, one active session at a time. No "abandon and restart" option; they must wait for the 4-hour auto-abandonment or complete the session.
- If an `in_progress` session exists but is older than 4 hours, mark it as `abandoned` (set `status="abandoned"`, `abandoned_at=now()`), then proceed as normal.
- If not eligible (28-day rule): show a message explaining when they can next participate (with countdown).
- If eligible: show the session environment guidelines (§4.2) with acknowledgement checkbox and a **"What device are you using?"** radio group (Desktop / Laptop / Tablet / Phone).
- **Mobile/tablet warning:** if the participant selects "Phone" or "Tablet", show a prominent warning: *"This study works best on a desktop or laptop with a physical keyboard. You can continue on this device, but your experience may be affected and timing data may be less reliable."* Allow them to proceed (don't block  –  some participants only have mobile), but the self-reported device type is a covariate that lets analysts account for it.
- On POST (acknowledged): create a `CodeSession` record with `device_type` from the form. Call `log_audit_event("session_started", participant, actor=request.user, session_id=session.pk)`. `pyodide_load_ms` and `editor_ready` are updated later by the client via JS callbacks once the editor initialises. Run the challenge selection algorithm (Action 4.3), create `CodeSessionChallenge` rows linking the selected challenges in position order, redirect to the first challenge.
- **Concurrent session creation guard:** wrap the "check for existing in_progress session → create new session" sequence in `transaction.atomic()` with `select_for_update()` on the Participant row. This prevents two browser tabs from racing past the check simultaneously and both creating an `in_progress` session. The lock is held only for the duration of the session creation transaction, so it doesn't affect other queries. Write a test that simulates concurrent session creation and asserts only one `in_progress` session exists.
- **Verify:** 28-day enforcement works (test with recent session). Withdrawn participant is blocked. Environment guidelines displayed. Device type saved. Mobile/tablet warning shown when appropriate. CodeSession created with correct `CodeSessionChallenge` entries. Concurrent tab session creation produces only one session.

### Action 5.2  –  Challenge Attempt View (Single-Page Session with HTMX) ✅
**Depends on:** 4.2, 5.1
**Description:** Build the main session page. The entire session (challenges, reflections, "another?" prompts) lives at **one URL** (e.g. `/sessions/<id>/`). Transitions between states use **HTMX partial swaps**  –  no full page reloads during a session. The code editor and Pyodide remain in vanilla JS (HTMX doesn't apply there).
- **Session page layout:** a persistent container with the code editor area. HTMX swaps content within a target div for transitions.
- **Challenge display:** the view determines the current challenge by finding the lowest `CodeSessionChallenge.position` that has no corresponding `ChallengeAttempt` for this session. The client never chooses which challenge to show  –  the server drives the sequence strictly by position order (1, 2, 3, …). Display: challenge description, skeleton code in CodeMirror, visible timer (mm:ss, toggleable), progress indicator ("Challenge 3 of 10"), "Submit" and "Skip" buttons, subtle "Stop session" link in corner.
- **On Submit:** JS executes tests via Pyodide (client-side), collects results (tests_passed, tests_total, timing, telemetry), then JS triggers an HTMX POST to the same session URL with the results as form data. Include the client-generated `attempt_uuid` (UUID v4, generated when the challenge is first displayed). Server-side submission service performs integrity checks **before** creating the attempt: (0) session status  –  session must be `in_progress`, otherwise return **409 Conflict** with an HTMX partial explaining the session has ended (see below); (1) `attempt_uuid` idempotency  –  if found, return existing result; (2) participant consistency  –  `request.user.participant == session.participant`; (3) challenge assignment  –  challenge is in this session's `CodeSessionChallenge` set; (4) position ordering  –  this challenge is at the next unattempted position (see Action 1.4 constraints). If any check fails, return 400 with a clear error. Otherwise create the `ChallengeAttempt` and return the reflection questions partial.
- **Attempt POST on completed/abandoned session:** if a submit or skip arrives for a session whose status is `completed` or `abandoned` (e.g. the 4-hour cleanup ran while the participant was idle, or they submitted the post-session survey in another tab), the server **rejects** the attempt with 409 and returns an HTMX partial: *"This session has ended. Your work on this challenge was not recorded."* with a link to the session start page. The attempt is **not** created  –  accepting stale attempts would corrupt timing data and violate the session state machine. Write tests: attempt POST on a `completed` session returns 409; attempt POST on an `abandoned` session returns 409; the response contains an informative message.
- **On Skip:** HTMX POST to the same URL with `skipped=True`. Server creates `ChallengeAttempt` with `skipped=True`, returns the reflection questions partial.
- **On "Stop session":** confirm dialog (JS), then HTMX POST to the same URL with `action=stop`. Server records current challenge as skipped, returns the post-session survey partial.
- The view detects `request.headers.get("HX-Request")` and returns the appropriate partial (`partials/_reflection.html`, `partials/_another_prompt.html`, `partials/_next_challenge.html`, `partials/_post_session_survey.html`) depending on the action and session state.
- **Auto-save drafts:** periodically (every 30 seconds) save the current editor content to `localStorage` keyed by `attempt_uuid`. On page reload or session resume, restore the draft. Clear the draft on successful submit or skip. This prevents lost work from browser crashes.
- **Pyodide load failure:** if Pyodide fails to load (CDN blocked, WASM error), show a clear error message: *"The code execution environment couldn't load. Please check your internet connection and reload the page."* with a "Reload" button. Do not start the timer until Pyodide is ready. If the failure persists, allow the participant to skip the challenge or stop the session without penalty (the attempt is not counted).
- **HTMX swap failure:** if an HTMX POST fails (network drop), show a Bulma notification: *"Connection lost. Your work is saved locally. Retrying…"* with automatic retry (HTMX's built-in `hx-trigger="retry"` or a JS retry). The idempotency key ensures retries are safe.
- **Browser back button:** use `hx-push-url="false"` on HTMX swaps within the session page so the browser history is not polluted. The back button takes the user out of the session (with a "leave session?" confirm via `beforeunload` event), not between HTMX states.
- **Verify:** Full challenge flow works without page reloads: see challenge → write code → submit → results + reflection questions → another/done. All data saved correctly. Skip and stop-session paths work. Draft auto-save and restore works after page reload. Pyodide failure shows recovery UI. Network failure retries gracefully.

### Action 5.3  –  Post-Challenge Reflection Questions (HTMX Partial) ✅
**Depends on:** 3.2, 5.2
**Description:** After each challenge attempt, HTMX swaps in the reflection questions.
- Server returns `partials/_reflection.html` containing active `SurveyQuestion` entries with `context="post_challenge"`, rendered via the reusable question renderer.
- On submit: HTMX POST to the same session URL. Server creates `SurveyResponse` entries linked to the `ChallengeAttempt`, returns `partials/_another_prompt.html`.
- Optional: participant can skip the reflection (HTMX POST with `action=skip_reflection`), goes straight to the "another?" prompt.
- "Another?" prompt: [ Another challenge ] triggers HTMX GET that swaps in the next challenge partial. [ I'm done for today ] triggers HTMX POST that returns the post-session survey partial.
- On 10th challenge: show session-complete message instead of "another?" prompt.
- **Verify:** Reflection questions appear after each attempt via HTMX swap. Responses saved with correct FK. Skipping works. Another/done routing works. No full page reloads.

### Action 5.4  –  Post-Session Survey and Session Completion (HTMX Partial) ✅
**Depends on:** 3.2, 5.2
**Description:** Build the post-session habit survey as an HTMX partial.
- Server returns `partials/_post_session_survey.html` containing active `SurveyQuestion` entries with `context="post_session"`, rendered via the reusable question renderer.
- Include the optional distraction question: "Were you able to work without distractions?" (Yes / Mostly / No).
- On submit: HTMX POST to the same session URL. Server creates `SurveyResponse` entries linked to the `CodeSession`. Mark `CodeSession.completed_at`, set `status="completed"`. Update `CodeSession.challenges_attempted`. Call `log_audit_event("session_completed", participant, actor=request.user, session_id=session.pk)`. Return a redirect header (`HX-Redirect`) to the personal results dashboard.
- **Verify:** Post-session survey appears via HTMX swap after ending a session. Responses saved. CodeSession marked complete. Redirects to results page.

---

## Phase 6: Results and Dashboard

### Action 6.1  –  Personal Results Page ✅
**Depends on:** 1.4, 5.4
**Description:** Build a basic personal results page for the participant.
- Show a table/list of past sessions: date, challenges attempted, average accuracy, average time.
- Show a simple line chart (Chart.js or Plotly.js) of accuracy over sessions.
- Show a simple line chart of average speed over sessions.
- Use a colourblind-friendly palette. Include text summary below each chart.
- Accessible: charts have `aria-label`, data table alternative available.
- **Caching:** cache per-participant dashboard data for 10 minutes (invalidated on new session completion). Use Django's per-view cache with a key based on `participant.pk` + `participant.profile_updated_at`.
- **Verify:** Participant with 2+ sessions sees charts with data points. Participant with 0 sessions sees an encouraging "complete your first session" message.

### Action 6.2  –  Front-Page Landing Page ✅
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

### Action 6.3  –  Sponsor Model ✅
**Depends on:** 0.5
**Description:** Create a simple `Sponsor` model for the front page.
- Fields: name, logo (ImageField), url, tier (CharField, optional), display_order, is_active.
- Register in admin.
- **Verify:** Can add sponsors in admin. They render on the landing page in order.

---

## Phase 7: Admin and Data Management ✅

### Action 7.1  –  Admin Dashboard ✅
**Depends on:** 1.1, 1.2, 1.3, 1.4
**Description:** Enhance the Django admin for study management.
- Participant admin: show consent status, profile completion, session count, last session date.
- CodeSession admin: list with participant, date, challenges attempted, completion status.
- ChallengeAttempt admin: show participant, challenge, accuracy, time, integrity fields (paste_count etc).
- SurveyQuestion admin: filter by context, is_active. Drag-to-reorder if feasible (django-admin-sortable2), otherwise display_order field.
- ConsentDocument admin: show version, is_active, published_at. Warn if creating a new active version (existing participants will need re-consent).
- Add export-to-CSV actions where relevant (consent records, survey responses, challenge attempts).
- **Permissions and audit logging:**
  – Install `django-simple-history` for audit logging on sensitive models: `ConsentDocument`, `SurveyQuestion`, `Challenge`. This records who changed what and when, critical for research instrument integrity.
  – Define custom permissions: `can_export_data` (for CSV export actions and dataset export), `can_edit_survey_questions`, `can_edit_consent_documents`, `can_process_deletion` (for processing deletion requests).
  – Assign permissions to appropriate groups (e.g. "Researcher" group gets export permissions, "Study Admin" gets all).
  – ConsentDocument and SurveyQuestion should be read-only for non-superusers without the explicit edit permission.
- **Verify:** All admin views load with correct data. Filters work. CSV exports produce valid files. History tab shows changes on ConsentDocument/SurveyQuestion/Challenge. Staff without `can_edit_consent_documents` cannot modify consent text. Deletion processing requires `can_process_deletion`.

### Action 7.2  –  Reminder Email System (Huey) ✅
**Depends on:** 1.1, 1.2
**Description:** Implement opt-in monthly reminder emails.
- Create a Huey periodic task that runs daily.
- For each participant where: `has_active_consent=True`, has `OptionalConsentRecord` for `reminder_emails` with `consented=True`, last completed session was > 28 days ago, no reminder sent in the last 28 days.
- Send a simple email: "It's been a while  –  ready for your next coding session?" with link to the app.
- **One-click unsubscribe:** every reminder email includes an unsubscribe link (tokenised, no login required) that sets `OptionalConsentRecord.consented=False` and `withdrawn_at=now()` for `consent_type="reminder_emails"`. Also include a `List-Unsubscribe` header for email client integration.
- Log reminder sends in a `ReminderLog` model (participant, sent_at) to avoid duplicate sends.
- Business logic in `helpers/task_helpers.py`, Huey task in `tasks.py` (per guidelines).
- **Verify:** Huey task runs. Eligible participants receive email. Ineligible participants don't. No duplicate sends. Unsubscribe link works without login. Unsubscribed participant stops receiving emails.

### Action 7.3  –  Abandoned Session Cleanup (Huey) ✅
**Depends on:** 1.4, 1.5, 1.6
**Description:** Create a Huey periodic task to mark stale sessions as abandoned.
- Runs hourly. Read `SESSION_TIMEOUT_HOURS` from `settings.STUDY` (Action 1.5). Find all `CodeSession` records where `status="in_progress"` and `started_at` is more than that many hours ago.
- Sets `status="abandoned"`, `abandoned_at=now()`. Call `log_audit_event("session_abandoned", participant, session_id=session.pk)` for each.
- Business logic in `helpers/task_helpers.py`, Huey task in `tasks.py` (per guidelines).
- **Verify:** Create a session with `started_at` 5 hours ago. Run the task. CodeSession status is now `abandoned`. AuditEvent for `session_abandoned` is created. A CodeSession started 1 hour ago is untouched.

### Action 7.4  –  PII Retention Cleanup (Huey) ✅
**Depends on:** 1.2, 1.4
**Description:** Create a Huey periodic task that purges retained PII after the 24-month retention period (see §7.5 of plan).
- Runs weekly. Finds `ConsentRecord` rows where `consented_at` is more than 24 months ago and `ip_address` is not null/blank. Sets `ip_address = None`, `user_agent = ""`.
- CodeSession model no longer stores any PII (device type is self-reported, no UA/browser/OS/timezone/screen data), so no session-level cleanup is needed.
- Business logic in `helpers/task_helpers.py`, Huey task in `tasks.py` (per guidelines).
- **Verify:** Create a consent record dated 25 months ago with an IP. Run the task. IP is now null, user_agent is blank. A record from 6 months ago is untouched.

### Action 7.5  –  Anonymised Dataset Export Command ✅
**Depends on:** 1.1, 1.2, 1.3, 1.4
**Description:** Build a reproducible, versioned management command for anonymised dataset export (see §12.4 of plan).
- Create management command `export_dataset` in a suitable app (e.g. `dashboard` or a new `exports` app).
- **Anonymisation logic** (in a helper module per guidelines):
  – Map `Participant.pk` → stable opaque ID using `HMAC-SHA256(EXPORT_SECRET_KEY, pk)`. Add `EXPORT_SECRET_KEY` to settings (env var, separate from `SECRET_KEY`).
  – Strip PII fields: email, username, IP address, user agent.
  – Coarsen: age → age band, geography → region/continent, timestamps → date only.
  – Exclude think-aloud transcripts unless participant has `transcript_sharing` optional consent.
  – Exclude withdrawn participants (filter by withdrawal timestamp).
  – Exclude admin/staff users.
- **Export tables** (one CSV + one Parquet per table): Participants (anonymised), CodeSessions, CodeSessionChallenges, ChallengeAttempts, Challenges, SurveyQuestions, SurveyResponses (with opaque participant ID).
- **Auto-generate `codebook.csv`**: for each exported file, list every column with: file name, column name, data type, description, allowed values (for choice fields).
- **Write `manifest.json`**: dataset version (`vYYYY-MM-DD`), row counts per file, SHA-256 checksum per file, export timestamp, git commit hash (via `subprocess`).
- Output directory: `exports/vYYYY-MM-DD/`. Command accepts `--output-dir` override.
- Add `pyarrow` to dependencies (for Parquet export).
- On successful export, call `log_audit_event("dataset_export_run", actor=None, version=version_slug, row_counts=manifest_counts)`.
- **Verify:** Running `uv run python manage.py export_dataset` produces a complete export directory. AuditEvent for `dataset_export_run` is created. Opaque IDs are stable across re-runs. No PII in exported files  –  write tests that scan all exported files for: email patterns (`*@*.*`), IPv4 patterns (`\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}`), and raw user agent substrings (`Mozilla/`, `Chrome/`, `Safari/`). Codebook covers all columns. Manifest checksums match file contents.

### Action 7.6  –  Dataset Download View and Embargo Enforcement ✅
**Depends on:** 7.5, 1.4
**Description:** Build the gated dataset download view and embargo enforcement.
- **Embargo start date** is derived at query time: `CodeSession.objects.filter(status="completed").order_by("completed_at").values_list("completed_at", flat=True).first()`. No stored setting needed.
- Create a `DatasetAccessGrant` model: user (FK, nullable  –  for registered researchers), email (for external requests), granted_by (FK → staff user), granted_at, reason (TextField). Register in admin.
- Create a dataset download page at `/data/` showing: embargo status (active/lifted), embargo start date, expected lift date, available dataset versions (list of `exports/v*/manifest.json`).
- Download links (e.g. `/data/download/v2027-03-15/`) are served via a Django view (not static files):
  – Check user is authenticated.
  – If embargo is active (current date < `EMBARGO_START_DATE + 12 months`): check for a `DatasetAccessGrant` for this user. If no grant, return 403 with a message showing when the embargo lifts.
  – If embargo has lifted (or user has a grant): serve the zipped export directory using `FileResponse` with `Content-Disposition: attachment`.
  – Dataset files are stored outside `STATIC_ROOT` and `MEDIA_ROOT`  –  not publicly accessible.
- **Post-embargo auto-generation:** add a Huey periodic task that runs on the 1st of each quarter (Jan, Apr, Jul, Oct). It runs the `export_dataset` management command and stores the output in the exports directory. Business logic in `helpers/task_helpers.py`.
- **Verify:** Unauthenticated user gets redirected to login. Authenticated user during embargo sees 403 with lift date. User with `DatasetAccessGrant` can download during embargo. After embargo, any authenticated participant can download. Dataset files are not accessible via direct URL guessing. Quarterly export task runs correctly.

---

## Phase 8: Pyodide and Client-Side Polish ✅

### Action 8.1  –  Pyodide Web Worker ✅
**Depends on:** 4.2
**Description:** Move Pyodide execution into a Web Worker for non-blocking UI.
- Create a Web Worker that loads Pyodide and accepts code + test cases via `postMessage`.
- Worker runs code, executes test cases, returns results (pass/fail per test, stdout, stderr, elapsed time).
- Main thread shows a "Running..." spinner while waiting.
- Handle timeout: if code runs for >30 seconds, kill the worker and show a timeout message.
- Handle errors: syntax errors, runtime errors  –  display clearly to the participant.
- **Verify:** Code execution doesn't freeze the UI. Timeout works. Errors display correctly.

### Action 8.2  –  Editor Telemetry ✅
**Depends on:** 4.2
**Description:** Wire up the client-side telemetry capture to the editor.
- Attach event listeners to CodeMirror: `paste` event (count + char length via clipboardData), keystroke count, tab `blur`/`focus` events.
- Track idle: detect tab blur >30s and no keystroke for >2min. Accumulate `idle_time_seconds`.
- Compute `active_time_seconds = time_taken_seconds – idle_time_seconds`.
- On submit: include all telemetry fields in the POST payload.
- **Verify:** Paste a block of code → paste_count and paste_total_chars are correct. Switch tabs → tab_blur_count increments. Idle time accumulates correctly.

---

## Phase 9: Front-Page Aggregate Graphs ✅

### Action 9.1  –  Aggregate Data API Endpoints ✅
**Depends on:** 1.4
**Description:** Create JSON API endpoints for front-page charts.
- `/api/stats/summary/`  –  total participants, sessions, challenges solved.
- `/api/stats/accuracy-over-time/`  –  average accuracy per month across all participants.
- `/api/stats/accuracy-by-vibe-coding/`  –  average accuracy over time, split by vibe-coding intensity (low/medium/high based on latest `post_session` vibe_coding_pct response).
- **Exclude staff/superusers** from all aggregate queries (filter `participant__user__is_staff=False, participant__user__is_superuser=False`). Also exclude withdrawn participants. This prevents admin testing from polluting public stats.
- Cache responses (5-minute TTL) using Django's cache framework.
- Only return aggregate data with group sizes >= 10.
- **Verify:** Endpoints return valid JSON. Caching works. Small group sizes are excluded. Staff participant data does not appear in aggregates.

### Action 9.2  –  Front-Page Charts ✅
**Depends on:** 6.2, 9.1
**Description:** Wire up the landing page charts to the API.
- Use Chart.js or Plotly.js.
- "The Big Question" chart: accuracy over time for high vs. low vibe-coders (from `/api/stats/accuracy-by-vibe-coding/`).
- Participation stats: live numbers from `/api/stats/summary/`.
- Colourblind-friendly palette. Text summary below each chart. Responsive.
- Graceful fallback when insufficient data: show "We need more participants to show trends  –  join the study!" message.
- **Verify:** Charts render with test data. Fallback message shows with no data. Accessible: text alternatives present.

---

## Phase 10: Deployment

### Action 10.1  –  Dockerise the Application ✅
**Depends on:** all prior actions
**Description:** Create Docker configuration for production deployment.
- `Dockerfile`: Python 3.13, install dependencies, collect static, gunicorn.
- `docker-compose.yml`: Django app, PostgreSQL, Redis (for Huey), Huey worker.
- `.env.example` with all required environment variables.
- Configure static file serving (whitenoise or nginx).
- Configure media file storage (local volume or S3-compatible for audio files later).
- **Verify:** `docker-compose up` starts all services. App is accessible. Migrations run. Huey worker processes tasks.

### Action 10.2  –  Rollbar Error Tracking (Production Only) ✅
**Depends on:** 10.1
**Description:** Set up Rollbar for production error tracking.
- Install `django-rollbar`. Add to `pyproject.toml`.
- Configure in `production.py` only: add Rollbar middleware, set `ROLLBAR` settings dict with `access_token` from env var (`ROLLBAR_ACCESS_TOKEN`), environment name, root path.
- Do **not** add Rollbar config to `local.py`  –  it must not run in local dev.
- Add `ROLLBAR_ACCESS_TOKEN` to `.env.example`.
- **Verify:** In production settings, Rollbar middleware is present. In local settings, it is not. Triggering a test error in production sends it to the Rollbar dashboard.

### Action 10.3  –  Structured Logging, Metrics, and Backups ✅
**Depends on:** 10.1
**Description:** Set up production observability and backup strategy.
- **Structured logging:**
  – Install `python-json-logger`. Configure Django's `LOGGING` in `production.py` to output JSON-formatted logs.
  – `local.py` uses standard console logging (human-readable).
  – Log key events at INFO level: session start/complete/abandon, challenge attempt submit, consent given/withdrawn, deletion processed, export run, reminder sent.
- **Key metrics model:**
  – Create a simple `MetricEvent` model (or use Django's cache-based counters): event_type (CharField), count (IntegerField), recorded_at (DateField). Track: sessions started/completed/abandoned per day, attempts submitted, Pyodide load failures (reported from client via a lightweight POST endpoint), export runs, reminder emails sent, deletion requests processed.
  – Add an admin dashboard widget or simple admin list view showing daily/weekly counts.
- **Email backend:**
  – `local.py`: `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` (prints to terminal).
  – `production.py`: SMTP or transactional service (Mailgun/Postmark) via env vars (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`).
  – Add all email env vars to `.env.example`.
- **Database backups:**
  – Configure automated daily PostgreSQL backups via Appliku's managed backup feature (or a cron script running `pg_dump` to S3-compatible object storage).
  – Document restore procedure in a `docs/backup-restore.md`.
  – Schedule quarterly restore test (manual  –  add to project README as an ops checklist item).
- **Verify:** Production logs are JSON-formatted. Metrics increment on key events. Email sends work (test with a reminder trigger). Backup runs and produces a valid dump.

### Action 10.4  –  Appliku / Hetzner Deployment ✅
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

## Phase 11: Pre-Launch

### Action 11.1  –  Privacy Policy and Terms ✅
**Depends on:** 2.2
**Description:** Create the privacy policy and terms of participation pages.
- Create a `PrivacyPolicy` model (like `ConsentDocument`): version, title, body (markdown), is_active, published_at. Admin-editable. Rendered via `|render_markdown|safe` in templates.
- Create views at `/privacy/` and `/terms/`. Footer links point here.
- Content must cover: what data is collected (list all fields), how it's stored, who can access it, retention periods (24-month PII purge), anonymised dataset release, participant rights (withdrawal, deletion), GDPR compliance, cookies (session cookie only, no tracking), contact details.
- Version the privacy policy the same way as consent documents  –  show version and last-updated date on the page.
- **Verify:** Privacy policy page loads. Footer link works. Admin can update the text. Version number displays.

### Action 11.2  –  Seed Data for Demo / Testing ✅
**Depends on:** all models
**Description:** Create a management command that generates realistic fake data for testing and demos.
- Create 20 fake participants with varied profiles (mark them as non-staff so they appear in aggregates).
- Each participant has 1–5 sessions with 3–10 challenge attempts each.
- Vary accuracy and timing realistically by tier.
- Include varied vibe-coding percentages in survey responses.
- Include 1 withdrawn participant and 1 with a deletion request (to test those flows).
- **Verify:** Running the command populates the database. Charts on the front page and personal dashboards render with realistic-looking data. Withdrawn participant is excluded from aggregates.

### Action 11.3  –  Accessibility Audit ✅
**Depends on:** all UI actions
**Description:** Audit all pages against WCAG 2.1 AA.
- Run automated tools (axe-core, Lighthouse accessibility audit) on every page.
- Manual checks: keyboard navigation through entire session flow, screen reader testing, colour contrast verification.
- Fix any issues found.
- **Verify:** Lighthouse accessibility score >= 90 on all pages. Full session flow completable via keyboard only.

### Action 11.4  –  Pilot Test (Closed Beta) 📋 MANUAL
**Depends on:** 10.4, 11.2
**Description:** Run a closed pilot with 5–10 trusted testers before public launch.
- Recruit testers (colleagues, friends, the dev team) who span different experience levels and devices.
- Each tester completes the full flow: registration → consent → profile → 1 session (3+ challenges) → post-session → view results.
- Collect structured feedback via a short post-pilot survey (can be a simple Google Form or an in-app survey): usability issues, confusing wording, bugs, timing experience, device used.
- Review all data created: check for data integrity issues, constraint violations, edge cases.
- Run the export command and verify the output is clean.
- Fix all issues found. This may loop back to earlier actions.
- **Verify:** All pilot testers complete the flow without blocking issues. No data integrity problems. Export produces valid, PII-free output. Feedback is addressed.

### Action 11.5  –  Pre-Registration (OSF) 📋 MANUAL
**Depends on:** 11.4
**Description:** Pre-register the study analysis plan before public launch.
- Draft a pre-registration document covering: research questions, hypotheses, primary outcome variables, statistical model (Bayesian multilevel regression), covariates, sample size expectations, exclusion criteria (cheating flags, abandoned sessions), sensitivity analyses.
- Register on the **Open Science Framework (OSF)** at osf.io. This creates a timestamped, immutable record of the analysis plan before data collection begins.
- Link the pre-registration URL in the study's "About" page and in the dataset's `manifest.json`.
- This is a **research credibility requirement**, not a code task  –  but it must happen before public launch.
- **Verify:** Pre-registration is publicly visible on OSF with a DOI. Link appears on the about page.

### Action 11.6  –  End-to-End Smoke Test 📋 MANUAL
**Depends on:** all prior actions
**Description:** Walk through the complete user journey on production and verify.
- Register new account → consent → intake questionnaire → start session → complete 3 challenges with reflection questions → stop session → post-session survey → view results → log out → log back in → verify 28-day enforcement.
- Test withdrawal flow: withdraw → request deletion → admin processes deletion.
- Test mobile warning: select "Phone" as device → warning appears → can still proceed.
- Test email: trigger a reminder → unsubscribe link works.
- Check admin: all records created correctly (participant, consent, survey responses, session, challenge attempts).
- Check front page: stats update (excluding staff data).
- Check privacy policy page.
- **Verify:** Zero errors in the full flow. All data persists correctly. Staff data excluded from public stats.

---

## Deferred to Post-MVP

The following items are acknowledged but intentionally deferred. They are documented here so they are not forgotten.

| Item | Why deferred | When to revisit |
|------|-------------|-----------------|
| **Think-aloud recording** (audio capture, upload, transcription, `ThinkAloudRecording` model) | Complex infrastructure (MediaRecorder API, file storage, STT integration). The model is already designed in the plan (§5.1b) and the `think_aloud_active` field exists on `ChallengeAttempt`. | Phase 2  –  after MVP is stable and ethics approval covers audio collection. |
| **Cheating detection reporting** (admin views for flagged attempts, paste-ratio dashboards) | Telemetry is captured at MVP. Analysis and flagging happen at analysis time, not in-app. | Phase 2  –  when enough data exists for meaningful outlier detection. |
| **Multi-account detection** (IP/behavioural heuristics) | Complex, false-positive-prone, and not critical for initial data collection. Email verification provides basic protection. | Phase 3  –  if data analysis reveals suspicious patterns. |
| **Retention incentives** (badges, streaks, email summaries with personal stats) | Nice-to-have for engagement but not required for data collection. Basic personal dashboard exists. | Phase 2  –  based on pilot feedback on participant motivation. |
| **Adaptive difficulty** (selecting challenges based on prior performance) | Random selection is the research baseline. Adaptive testing is a future enhancement. | Phase 3  –  requires IRT model calibration from collected data. |
| **Community features** (Discord setup, "Get Involved" page content, collaborator interest form) | External service setup, not a code task. Footer links are in place. | Pre-launch  –  setup Discord server and GitHub Discussions manually. |
| **Admin runbook** (deletion processing, cheating investigation, export procedures, participant complaint handling) | Operational documentation, not code. | Pre-launch  –  write alongside pilot testing. |
