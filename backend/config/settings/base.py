"""Base settings. All environment-specific values come from environment variables."""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(_env_file)

SECRET_KEY = env("DJANGO_SECRET_KEY")
# Key for application-level encryption of stored secrets (Fernet). Required; rotate with care.
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")
# Key material for HMAC of stored credentials and codes. Defaults to SECRET_KEY.
CREDENTIAL_PEPPER = env("CREDENTIAL_PEPPER", default=SECRET_KEY)
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])
BEHIND_PROXY = env.bool("DJANGO_BEHIND_PROXY", default=False)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "apps.common",
    "apps.users",
    "apps.estates",
    "apps.properties",
    "apps.residents",
    "apps.audit_logs",
    "apps.authentication",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
# Sensitive operations use explicit transaction.atomic() in the service layer.
DATABASES["default"]["ATOMIC_REQUESTS"] = False
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = env("REDIS_URL", default="")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

AUTH_USER_MODEL = "users.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "EXCEPTION_HANDLER": "apps.common.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/min",
        "user": "600/min",
        "login": "10/min",
        "two_factor": "10/min",
        "password_reset": "5/min",
        "resident_registration": "5/hour",
    },
    # Client IP is the socket address unless exactly one trusted proxy sits in front.
    "NUM_PROXIES": 1 if BEHIND_PROXY else 0,
}

# Authentication policy
TWO_FACTOR = {
    "ISSUER": "Estate Access",
    "CHALLENGE_MAX_AGE": 300,  # seconds a password-verified sign-in may wait for its 2FA step
    # Estate roles that use the management dashboard and therefore need 2FA.
    # Platform administrators always need it.
    "ROLES": ["estate_admin", "estate_manager"],
}
PASSWORD_RESET = {"CODE_TTL_MINUTES": 30, "MAX_FAILED_ATTEMPTS": 5}
LOGIN_LOCKOUT = {"MAX_FAILURES": 5, "WINDOW_SECONDS": 900}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Estate Access Platform API",
    "DESCRIPTION": "Visitor access management for residential estates.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "EstateStatusEnum": "apps.estates.models.EstateStatus.choices",
        "MembershipStatusEnum": "apps.estates.models.MembershipStatus.choices",
        "PropertyStatusEnum": "apps.properties.models.PropertyStatus.choices",
        "ResidentStatusEnum": "apps.residents.models.ResidentStatus.choices",
        "ResidentDocumentStatusEnum": "apps.residents.models.ResidentDocumentStatus.choices",
        "ResidentAssignmentStatusEnum": "apps.residents.models.AssignmentStatus.choices",
        "ResidentDocumentTypeEnum": "apps.residents.models.ResidentDocumentType.choices",
    },
}
API_DOCS_ENABLED = env.bool("API_DOCS_ENABLED", default=DEBUG)

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL or "memory://")
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TIMEZONE = TIME_ZONE

# Transport security (production)
if BEHIND_PROXY:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=not DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 0 if DEBUG else env.int("DJANGO_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO")},
}
