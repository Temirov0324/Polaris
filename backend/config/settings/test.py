from .dev import *  # noqa: F401,F403

# Tests must not depend on a running Redis instance.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Tests don't run collectstatic, so the manifest-hashed storage used in
# dev/prod (whitenoise.storage.CompressedManifestStaticFilesStorage) would
# make any test that renders a full admin/Jazzmin page (e.g. via the
# Django test client) fail with "Missing staticfiles manifest entry" —
# swap in the plain storage, which resolves {% static %} without a manifest.
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}
