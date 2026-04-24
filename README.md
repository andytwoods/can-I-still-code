# Can I Still Code: Coding Skill Longitudinal Assessment

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

Can I Still Code is a longitudinal, citizen-science research tool designed to measure whether **vibe coding** (AI-assisted coding) leads to coding skill degradation over time.

Participants periodically complete short Python coding challenges while self-reporting their coding habits. The resulting dataset supports **Bayesian multilevel regression** modelling and invites the broader community to contribute analyses.

> This codebase was developed with AI assistance (Claude) by a Django developer with 15+ years of experience. Scientific design, study protocol, and research decisions are the author's own.

## 🚀 Quick Start (Local Development)

This project uses `uv` for dependency management.

### 1. Prerequisites
- Python 3.14
- `uv` installed ([get uv](https://github.com/astral-sh/uv))
- Redis (for Huey background tasks)

### 2. Installation
Clone the repository and install dependencies:
```bash
uv sync
```

### 3. Local Setup
Run the one-shot setup command to create a superuser, seed challenges, and survey questions:
```bash
uv run python manage.py setup_app
```
*Note the generated superuser credentials in your terminal.*

### 4. Run the Application
Start the development server:
```bash
uv run python manage.py runserver
```
Visit `http://127.0.0.1:8000/` to get started.

### 5. Start Background Tasks (Huey)
In a separate terminal, start the Huey worker:
```bash
uv run python manage.py run_huey
```

---

## 🛠 Tech Stack

- **Backend:** Django (Python 3.14)
- **Frontend:** Bulma (CSS), HTMX (Partial updates), Vanilla JS (Pyodide integration)
- **Database:** SQLite (local), PostgreSQL (production)
- **Execution Engine:** Pyodide (WASM) for in-browser Python execution
- **Background Tasks:** Huey (Redis-backed)
- **Authentication:** django-allauth (Google/GitHub social login required in production)
- **Styling:** Bulma via `django-bulma` and `crispy-bulma`

---

## 🏗 Core Architecture

### 1. Longitudinal Assessment
- **Minimum 28 days between sessions** enforced server-side.
- **Up to 10 challenges per session**, presented in ascending difficulty.
- **In-browser execution:** Pyodide runs code client-side, results sent to server.

### 2. Unified Question System
A flexible model for profile intake, post-challenge reflections, and post-session habit surveys. All managed via the Django admin.

### 3. Citizen Science & Open Data
- Participants own their data and see rich trend visualizations.
- Fully anonymized dataset released quarterly (after a 12-month embargo).
- Built-in data export pipeline for researchers.

---

## 🧪 Testing & Quality

### Run Tests
```bash
uv run pytest
```

### Type Checking
```bash
uv run mypy agenticbrainrot
```

### Linting (Ruff)
```bash
uv run ruff check .
```

---


## 📦 Deployment

Deployed on **Hetzner** VPS via **Appliku**. Configuration is managed in `appliku.yaml`.
Production requires:
- `ROLLBAR_ACCESS_TOKEN` for error tracking.
- `POSTGRES_URL` for the database.
- `REDIS_URL` for Huey.
- Social login providers configured in Django Admin.

---

## 🤝 Contributing

We welcome collaborators! Check out the `high_level_plan.md` for our roadmap.
- **GitHub Discussions:** Primary channel for study design and analysis ideas.
- **Discord:** Community watercooler for casual conversation.
