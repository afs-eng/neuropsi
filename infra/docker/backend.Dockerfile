# ============================================================
# NeuroAvalia — Backend Dockerfile (Multi-stage: dev + prod)
# ============================================================

# --------------------------------------------------------
# Stage 1: Dev (montagem rapida com hot-reload)
# Usa volume bind mount (.:/app) — dependencias vao pro
# Python do sistema pra nao serem sobrescritas.
# --------------------------------------------------------
FROM python:3.12-slim AS dev

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1
ENV UV_NO_MANAGED_PYTHON=1
ENV UV_PYTHON=3.12
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv && rm -rf /root/.cache

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen && uv run python -m playwright install chromium

COPY . .
RUN chmod +x /app/infra/docker/backend.entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/infra/docker/backend.entrypoint.sh"]
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]

# --------------------------------------------------------
# Stage 2: Prod (otimizado para Gunicorn)
# Sem volume mount — usa .venv gerenciado pelo uv.
# --------------------------------------------------------
FROM python:3.12-slim AS prod

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PYTHON=3.12
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql-client \
    curl \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv && rm -rf /root/.cache

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev && uv run python -m playwright install chromium

COPY . .
RUN chmod +x /app/infra/docker/backend.entrypoint.sh

RUN uv run python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-file", "-"]
