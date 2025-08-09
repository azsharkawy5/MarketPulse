FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends curl netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Python deps manager
ENV POETRY_VIRTUALENVS_CREATE=0
RUN pip install --upgrade pip \
    && pip install "poetry>=1.5,<3.0"

# Install dependencies based on lockfile for better caching
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-interaction --no-ansi --only main --no-root

# Copy project source
COPY . /app

# Ensure logs directory exists (settings.py also creates it)
RUN mkdir -p /app/logs

EXPOSE 8000

# App server; migrations/static collection are handled via docker-compose command
CMD ["gunicorn", "MarketPulse.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]


