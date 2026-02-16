# ---------- build stage ----------
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only (no dev group)
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the project
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev

# ---------- runtime stage ----------
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# Copy the virtual environment and project from builder
COPY --from=builder /app /app

# Add the virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Collect static files (needs a dummy SECRET_KEY for collectstatic)
RUN DJANGO_SECRET_KEY=build-placeholder \
    DATABASE_URL=sqlite:///tmp/placeholder.db \
    DJANGO_ALLOWED_HOSTS=placeholder \
    DJANGO_ADMIN_URL=admin/ \
    ROLLBAR_ACCESS_TOKEN=placeholder \
    python manage.py collectstatic --noinput

EXPOSE 8000

# Make run.sh executable
RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]
