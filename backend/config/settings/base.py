"""
Base Django settings for the PolarisAI project.

Shared between dev.py and prod.py. Never import this module directly in
manage.py / wsgi.py — use DJANGO_SETTINGS_MODULE=config.settings.dev|prod.
"""
from datetime import timedelta
from pathlib import Path

import environ

# backend/config/settings/base.py -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "import_export",
    "django_celery_beat",
    # local apps
    "apps.users",
    "apps.destinations",
    "apps.trips",
    "apps.savings",
    "apps.chat",
    "apps.notifications",
    "apps.analytics",
    "apps.telegram_bot",
    "apps.admin_agent",
]

MIDDLEWARE = [
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
        "DIRS": [FRONTEND_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://travelai:travelai@localhost:5432/travelai"),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "users.User"

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# Fills the gaps Django's own (partial) uz admin catalog leaves empty, and
# translates strings from packages that ship no uz locale at all (jazzmin,
# django-celery-beat, simplejwt token_blacklist) — see locale/uz/LC_MESSAGES.
LOCALE_PATHS = [BASE_DIR / "locale"]

# The site itself authenticates via JWT-in-cookie (see apps.users), not
# Django sessions — session login is only ever used for /admin/, whose
# Jazzmin login template doesn't render a "next" field, so the default
# LOGIN_REDIRECT_URL ("/accounts/profile/") would otherwise land users
# back on the public frontend.
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [FRONTEND_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- REST framework -----------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.EnvelopePagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "core.exceptions.envelope_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "PolarisAI API",
    "DESCRIPTION": "Sayohat byudjeti va jamg'arish rejasi API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# --- Auth / JWT (httpOnly cookie) ---------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

AUTH_COOKIE_ACCESS = "access_token"
AUTH_COOKIE_REFRESH = "refresh_token"
AUTH_COOKIE_SECURE = env.bool("AUTH_COOKIE_SECURE", default=False)
AUTH_COOKIE_SAMESITE = "Lax"
AUTH_COOKIE_PATH = "/"

# --- Redis / Celery ------------------------------------------------------

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# --- Gemini (Google AI Studio) ---------------------------------------------

GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
GEMINI_MODEL = env("GEMINI_MODEL", default="gemini-3.6-flash")

# Separate key for the admin-only content agent (apps.admin_agent) — kept
# distinct from GEMINI_API_KEY above so usage/cost/rate-limits for the
# founder's catalog-entry tool never compete with the user-facing chat.
# Opt-in: leave empty to disable (the console shows a "not configured"
# message instead of erroring).
GEMINI_ADMIN_API_KEY = env("GEMINI_ADMIN_API_KEY", default="")

# --- Email (dev reminders) ------------------------------------------------

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="PolarisAI <noreply@polarisai.local>")

# Only used when EMAIL_BACKEND is the smtp backend — e.g. registration/
# password-reset codes need a real inbox to land in, which the console
# backend can't do (it just prints to server logs).
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)

# --- Error tracking (Sentry) ----------------------------------------------
# Opt-in only: nothing happens unless SENTRY_DSN is set in the environment.
# Free DSN: https://sentry.io -> New Project -> Django.

SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=env("SENTRY_ENVIRONMENT", default="production"),
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1),
        send_default_pii=False,
    )

# --- Telegram bot (notifications + /byudjet) --------------------------------
# Opt-in: leave TELEGRAM_BOT_TOKEN empty to disable entirely (sends become
# silent no-ops, webhook returns 404). Create a bot via @BotFather, then
# register the webhook once with:
#   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<domain>/api/v1/telegram/webhook/<TELEGRAM_WEBHOOK_SECRET>/"

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_BOT_USERNAME = env("TELEGRAM_BOT_USERNAME", default="")
TELEGRAM_WEBHOOK_SECRET = env("TELEGRAM_WEBHOOK_SECRET", default="")

# --- Admin panel look & feel (Jazzmin) --------------------------------------

JAZZMIN_SETTINGS = {
    "site_title": "PolarisAI Admin",
    "site_header": "PolarisAI",
    "site_brand": "PolarisAI",
    "welcome_sign": "PolarisAI boshqaruv paneliga xush kelibsiz",
    "copyright": "PolarisAI",
    "search_model": ["users.User", "trips.Trip", "destinations.Destination"],
    "topmenu_links": [
        {"name": "Saytni ko'rish", "url": "/", "new_window": True},
        {"name": "AI yordamchi", "url": "/admin/agent/", "icon": "fas fa-robot"},
        {"model": "users.User"},
    ],
    "show_sidebar": True,
    "navigation_expanded": False,
    "order_with_respect_to": [
        "analytics",
        "admin_agent",
        "users",
        "trips",
        "savings",
        "destinations",
        "chat",
        "auth",
        "django_celery_beat",
        "token_blacklist",
    ],
    "icons": {
        "auth.Group": "fas fa-users-cog",
        "users.User": "fas fa-user-astronaut",
        "trips.Trip": "fas fa-route",
        "trips.TripMember": "fas fa-user-friends",
        "savings.SavingEntry": "fas fa-piggy-bank",
        "destinations.Destination": "fas fa-map-marker-alt",
        "destinations.Country": "fas fa-flag",
        "destinations.PriceReference": "fas fa-tags",
        "chat.ChatMessage": "fas fa-comments",
        "analytics.AnalyticsEvent": "fas fa-chart-line",
        "admin_agent.AdminAgentLog": "fas fa-robot",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": "css/admin-polaris.css",
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
}

JAZZMIN_UI_TWEAKS = {
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_child_indent": True,
    "sidebar_nav_flat_style": True,
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "actions_sticky_top": True,
}
