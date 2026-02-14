# Actions: Implementation Breakdown

Each action is a self-contained chunk suitable for an agentic LLM to complete in one session. Actions are ordered by dependency — later actions build on earlier ones. Each action specifies what to build, what it depends on, and how to verify it works.

---

## Phase 0: Project Scaffolding

### Action 0.1 — Django Project Setup
**Depends on:** nothing
**Description:** Initialise the Django project with PostgreSQL, environment-based settings, and core dependencies.
- Run `django-admin startproject config .` (or equivalent).
- Create a `requirements.txt` / `pyproject.toml` with: Django, psycopg2-binary, django-allauth, django-huey, django-crispy-forms, crispy-bulma, python-dotenv (or django-environ).
- Configure `settings.py`: split into `base.py`, `local.py`, `production.py`. Use env vars for `SECRET_KEY`, `DATABASE_URL`, `DEBUG`, `ALLOWED_HOSTS`.
- Set up PostgreSQL as the default database.
- Add Bulma CSS via CDN in a `base.html` template.
- Create a `base.html` template with: Bulma CSS, skip-to-content link, semantic HTML structure (`<nav>`, `<main>`, `<footer>`), `{% block content %}`, CSRF token.
- Add a simple health-check view at `/` that renders "Hello world" to confirm everything works.
- **Verify:** `python manage.py runserver` starts, `/` returns 200, `python manage.py migrate` runs cleanly.

### Action 0.2 — Authentication (django-allauth)
**Depends on:** 0.1
**Description:** Set up django-allauth with Google and GitHub social login, plus email/password fallback.
- Install and configure django-allauth in settings (add to `INSTALLED_APPS`, `AUTHENTICATION_BACKENDS`, `MIDDLEWARE`).
- Configure allauth to require email verification (`ACCOUNT_EMAIL_VERIFICATION = "mandatory"`).
- Add Google and GitHub as social providers in settings. Use env vars for client IDs / secrets.
- Create allauth URL includes in `urls.py`.
- Override allauth templates to use Bulma styling and extend `base.html`.
- **Verify:** Registration, login, logout work via email/password. Social login config is present (full testing requires provider credentials). Email verification flow works (can use console email backend for local dev).

### Action 0.3 — Django App Structure
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
- **Verify:** `python manage.py check` passes. No models yet — just the app directories and empty files.

---

## Phase 1: Core Models

### Action 1.1 — Participant Model
**Depends on:** 0.2, 0.3
**Description:** Create the `Participant` model linked to Django's `User`.
- Fields: `user` (OneToOneField → User), `has_active_consent` (BooleanField, default False), `profile_completed` (BooleanField, default False), `profile_updated_at` (DateTimeField, nullable).
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
**Depends on:** 0.3
**Description:** Create the `SurveyQuestion` and `SurveyResponse` models.
- `SurveyQuestion`: text, help_text, question_type (choices: text/number/single_choice/multi_choice/scale), choices (JSONField, nullable), scale_min, scale_max, min_label, max_label, mid_label, context (choices: profile/post_challenge/post_session), category (nullable), is_required, is_active, display_order, created_at, updated_at.
- `SurveyResponse`: participant (FK), question (FK), value (TextField), answered_at, session (FK, nullable), challenge_attempt (FK, nullable), supersedes (FK self, nullable).
- Add `__str__` to both.
- Register in Django admin with filters by context, is_active, question_type.
- Run `makemigrations` and `migrate`.
- **Verify:** Can create questions in admin, create responses in the shell, filter questions by context.

### Action 1.4 — Challenge and Session Models
**Depends on:** 1.1
**Description:** Create the challenge and session models.
- `Challenge`: external_id, title, description (TextField, markdown), skeleton_code (TextField), test_cases (JSONField), difficulty (IntegerField, 1–5 for tiers), tags (JSONField), is_active (bool), created_at, updated_at.
- `Session`: participant (FK), started_at, completed_at (nullable), challenges_attempted (IntegerField, default 0), distraction_free (NullBooleanField), challenge_pool (JSONField — locked list of challenge IDs for this session).
- `ChallengeAttempt`: participant (FK), challenge (FK), session (FK), submitted_code (TextField), tests_passed (IntegerField), tests_total (IntegerField), time_taken_seconds (FloatField), active_time_seconds (FloatField), idle_time_seconds (FloatField), started_at, submitted_at, skipped (BooleanField), think_aloud_active (BooleanField, default False), paste_count (IntegerField, default 0), paste_total_chars (IntegerField, default 0), keystroke_count (IntegerField, default 0), tab_blur_count (IntegerField, default 0).
- Add `__str__` to all models.
- Register in Django admin.
- Add indexes on: `ChallengeAttempt.participant`, `ChallengeAttempt.session`, `Challenge.difficulty`, `Challenge.is_active`.
- Run `makemigrations` and `migrate`.
- **Verify:** Can create challenges in admin, create sessions and attempts in the shell.

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
- Allow partial saves (if the user navigates away, answered questions are saved).
- **Verify:** New user sees all 24 questions grouped by category. Submitting saves responses. Profile page is accessible again later for edits. Editing creates new `SurveyResponse` with `supersedes` pointing to old one.

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
- Sample randomly per tier distribution: 3 T1, 3 T2, 2 T3, 1 T4, 1 T5 (configurable — store distribution in Django settings or a site config model).
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
- Check: participant has active consent, profile completed, and >= 28 days since last completed session.
- If not eligible: show a message explaining when they can next participate (with countdown).
- If eligible: show the session environment guidelines (§4.2) with acknowledgement checkbox.
- On POST (acknowledged): create a `Session` record, run the challenge selection algorithm (Action 4.3), store the challenge pool on the session, redirect to the first challenge.
- **Verify:** 28-day enforcement works (test with recent session). Environment guidelines displayed. Session created with correct challenge pool.

### Action 5.2 — Challenge Attempt View
**Depends on:** 4.2, 5.1
**Description:** Build the main challenge-solving page.
- Display: challenge description, skeleton code in the code editor (CodeMirror), visible timer (mm:ss, toggleable), "Submit" and "Skip" buttons, subtle "Stop session" link in corner.
- On Submit: execute tests via Pyodide (client-side), collect results (tests_passed, tests_total, timing, telemetry), POST to server as JSON.
- Server-side: create `ChallengeAttempt` record with all fields.
- On Skip: create `ChallengeAttempt` with `skipped=True`, minimal timing data.
- On "Stop session": confirm dialog, record current challenge as skipped, redirect to post-session survey.
- After submission: show post-challenge reflection questions (Action 5.3), then the "another?" prompt.
- **Verify:** Full challenge flow works: see challenge → write code → submit → see results → reflection questions → another/done. All data saved correctly. Skip and stop-session paths work.

### Action 5.3 — Post-Challenge Reflection Questions
**Depends on:** 3.2, 5.2
**Description:** After each challenge attempt, show the post-challenge reflection questions.
- Fetch active `SurveyQuestion` entries with `context="post_challenge"`.
- Render using the reusable question renderer.
- On submit: create `SurveyResponse` entries linked to the `ChallengeAttempt`.
- Optional: participant can skip the reflection entirely.
- Then show the "Nice work! Ready for another?" prompt with [ Another challenge ] and [ I'm done for today ].
- On 10th challenge: show session-complete message instead.
- **Verify:** Reflection questions appear after each attempt. Responses saved with correct FK. Skipping works. Another/done routing works.

### Action 5.4 — Post-Session Survey and Session Completion
**Depends on:** 3.2, 5.2
**Description:** Build the post-session habit survey shown after the participant finishes.
- Fetch active `SurveyQuestion` entries with `context="post_session"`.
- Render using the reusable question renderer.
- On submit: create `SurveyResponse` entries linked to the `Session`. Mark `Session.completed_at`. Update `Session.challenges_attempted`.
- Include the optional distraction question: "Were you able to work without distractions?" (Yes / Mostly / No).
- Redirect to the personal results dashboard.
- **Verify:** Post-session survey appears after ending a session. Responses saved. Session marked complete. Redirect to results works.

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
**Depends on:** 0.3
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
- **Verify:** All admin views load with correct data. Filters work. CSV exports produce valid files.

### Action 7.2 — Reminder Email System (Huey)
**Depends on:** 1.1, 1.2
**Description:** Implement opt-in monthly reminder emails.
- Create a Huey periodic task that runs daily.
- For each participant where: `has_active_consent=True`, has `OptionalConsentRecord` for `reminder_emails` with `consented=True`, last completed session was > 28 days ago, no reminder sent in the last 28 days.
- Send a simple email: "It's been a while — ready for your next coding session?" with link to the app.
- Log reminder sends in a `ReminderLog` model (participant, sent_at) to avoid duplicate sends.
- Business logic in `helpers/task_helpers.py`, Huey task in `tasks.py` (per guidelines).
- **Verify:** Huey task runs. Eligible participants receive email. Ineligible participants don't. No duplicate sends.

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
- Cache responses (5-minute TTL) using Django's cache framework.
- Only return aggregate data with group sizes >= 10.
- **Verify:** Endpoints return valid JSON. Caching works. Small group sizes are excluded.

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
- `Dockerfile`: Python 3.11+, install dependencies, collect static, gunicorn.
- `docker-compose.yml`: Django app, PostgreSQL, Redis (for Huey), Huey worker.
- `.env.example` with all required environment variables.
- Configure static file serving (whitenoise or nginx).
- Configure media file storage (local volume or S3-compatible for audio files later).
- **Verify:** `docker-compose up` starts all services. App is accessible. Migrations run. Huey worker processes tasks.

### Action 10.2 — Appliku / Hetzner Deployment
**Depends on:** 10.1
**Description:** Deploy to Hetzner via Appliku.
- Configure Appliku project pointing to the repo.
- Set environment variables in Appliku dashboard.
- Configure PostgreSQL (Appliku managed or Hetzner-hosted).
- Set up SSL certificate.
- Configure DNS.
- Set up allauth social providers (Google, GitHub) with production redirect URIs.
- **Verify:** App is live at the production URL. Registration, consent, session flow all work. Social login works.

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
