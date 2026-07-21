from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)  # noqa: F405

# Dev iteration is fast and frequent — never let the browser cache CSS/JS
# between reloads. WhiteNoise sets Cache-Control from this value.
WHITENOISE_MAX_AGE = 0
