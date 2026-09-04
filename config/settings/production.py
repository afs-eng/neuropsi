from urllib.parse import urlparse

from .base import *


DEBUG = False


def _hostname_from_url(url: str) -> str:
    return urlparse(url).hostname or ""


def _append_unique(values: list[str], candidate: str) -> None:
    if candidate and candidate not in values:
        values.append(candidate)


render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
backend_public_url = os.getenv("BACKEND_PUBLIC_URL", "").strip()
frontend_base_url = os.getenv("FRONTEND_BASE_URL", "").strip()
allow_vercel_previews = env_bool("ALLOW_VERCEL_PREVIEWS", True)

ALLOWED_HOSTS = [
    "sistema-neuro.onrender.com",
    "neuro-k06p.onrender.com",
    ".onrender.com",
    "localhost",
    "127.0.0.1",
]
for host in env_list("ALLOWED_HOSTS"):
    _append_unique(ALLOWED_HOSTS, host)

_append_unique(ALLOWED_HOSTS, render_hostname)
_append_unique(ALLOWED_HOSTS, _hostname_from_url(backend_public_url))

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
if not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = ["https://sistema-neuro.onrender.com"]
if render_hostname:
    _append_unique(CSRF_TRUSTED_ORIGINS, f"https://{render_hostname}")
if backend_public_url:
    _append_unique(CSRF_TRUSTED_ORIGINS, backend_public_url)

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

# Mantemos as configurações originais para referência futura
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS") or []
if frontend_base_url:
    _append_unique(CORS_ALLOWED_ORIGINS, frontend_base_url)

CORS_ALLOWED_ORIGIN_REGEXES = []
if allow_vercel_previews:
    # Aceita qualquer domínio Vercel (subdomínios e hashes)
    CORS_ALLOWED_ORIGIN_REGEXES.append(r"^https://[a-zA-Z0-9._-]+\.vercel\.app$")
    _append_unique(CSRF_TRUSTED_ORIGINS, "https://*.vercel.app")

SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# No Render, URLs internas podem não requerer SSL
# Verificamos se DATABASE_URL contém o host interno (dpg-...)
db_url_env = os.getenv("DATABASE_URL", "")
is_internal_db = "dpg-" in db_url_env and "-a" in db_url_env

# Se estivermos no Render, forçamos o dj_database_url a usar psycopg
if db_url_env.startswith("postgres://"):
    db_url_env = db_url_env.replace("postgres://", "postgresql://", 1)

database_url = db_url_env or default_database_url
requires_ssl = database_url.startswith(("postgres://", "postgresql://")) and env_bool(
    "DATABASE_SSL_REQUIRE", not is_internal_db
)

DATABASES["default"] = dj_database_url.parse(
    database_url,
    conn_max_age=600,
    ssl_require=requires_ssl,
)

LOGGING["root"]["level"] = os.getenv("DJANGO_LOG_LEVEL", "INFO")
# Garante que erros de SQL apareçam no log do Render
LOGGING["loggers"] = {
    "django.db.backends": {
        "level": "ERROR",
        "handlers": ["console"],
    },
    "apps.accounts": {
        "level": "DEBUG",
        "handlers": ["console"],
    },
}
