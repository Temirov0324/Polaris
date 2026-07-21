"""Local dev without Docker/Postgres/Redis: point DATABASE_URL at SQLite
in your .env and run with --settings=config.settings.local. Celery tasks
run synchronously (no broker needed); cache is in-process memory."""
from .dev import *  # noqa: F401,F403

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
