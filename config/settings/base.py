"""Base Django settings shared across environments."""

from pathlib import Path
import os

import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name, "")
    items = [item.strip() for item in value.split(",") if item.strip()]
    if items:
        return items
    return default or []


_SECRET_KEY_ENV = os.getenv("SECRET_KEY", "")
if not _SECRET_KEY_ENV:
    if os.getenv("DEBUG", "").lower() == "false":
        raise ValueError("SECRET_KEY deve ser configurada em produção")
    _SECRET_KEY_ENV = "django-insecure-dev-only-fallback-not-for-production-use"

SECRET_KEY = _SECRET_KEY_ENV

DEBUG = env_bool("DEBUG", True)

# Desabilita redirecionamento automático de barra final para evitar conflitos
# entre rotas do Django Ninja com/sem trailing slash (causa erros 405)
APPEND_SLASH = False

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    ["127.0.0.1", "localhost"],
)

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    ["http://127.0.0.1:3000", "http://localhost:3000", "http://0.0.0.0:3000"],
)

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://127.0.0.1:8000")
ENABLE_PUBLIC_REGISTRATION = env_bool("ENABLE_PUBLIC_REGISTRATION", DEBUG)
ENABLE_SYSTEM_SETUP = env_bool("ENABLE_SYSTEM_SETUP", False)
SYSTEM_BOOTSTRAP_PASSWORD = os.getenv("SYSTEM_BOOTSTRAP_PASSWORD", "")
REDIS_URL = os.getenv("REDIS_URL", "").strip()

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# `django-tailwind` is an optional dev-time dependency. In some minimal
# production build environments the `tailwind` package may not be installed
# (causing import errors during `manage.py` execution). Detect availability
# and include it only when importable.
import importlib.util

if importlib.util.find_spec("tailwind") is not None:
    INSTALLED_APPS.append("tailwind")

INSTALLED_APPS += [
    "corsheaders",
    "apps.common",
    "apps.accounts",
    "apps.patients",
    "apps.evaluations",
    "apps.documents",
    "apps.anamnesis",
    "apps.messaging",
    "apps.tests",
    "apps.reports",
    "apps.api",
    "apps.ai",
    "apps.audit",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

default_database_url = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL", default_database_url),
        conn_max_age=600,
        ssl_require=env_bool("DATABASE_SSL_REQUIRE", False),
    )
}

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "neuro-local-cache",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@neuroavalia.local")

# --- Resend (e-mail transacional) ---
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv(
    "RESEND_FROM_EMAIL", "NeuroAvalia <onboarding@resend.dev>"
)

# --- Evolution API (WhatsApp automático) ---
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "")


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("openRouter_key", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_REFERER = os.getenv("OPENAI_REFERER", "")
OPENAI_TITLE = os.getenv("OPENAI_TITLE", "")
OPENAI_MODEL_TEXT = os.getenv("OPENAI_MODEL_TEXT", "gpt-4o")
OPENAI_MODEL_REASONING = os.getenv("OPENAI_MODEL_REASONING", "gpt-4o")
OPENAI_FALLBACK_MODELS = env_list("OPENAI_FALLBACK_MODELS")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL_TEXT = os.getenv("ANTHROPIC_MODEL_TEXT", "claude-3-7-sonnet-latest")
DEFAULT_AI_PROVIDER = "ollama" if os.getenv("DJANGO_ENV", "local") == "local" else "openai"
AI_PROVIDER = os.getenv("AI_PROVIDER", DEFAULT_AI_PROVIDER)
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    os.getenv("DOCKER_OLLAMA_BASE_URL", "http://localhost:11434"),
)
OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    os.getenv("DOCKER_OLLAMA_MODEL", "qwen3.5:9b"),
)
TEST_INTERPRETATION_AI_ENABLED = os.getenv("TEST_INTERPRETATION_AI_ENABLED", "false").lower() == "true"

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
    },
}

INTERNAL_IPS = ["127.0.0.1"]
