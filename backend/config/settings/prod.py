from .base import *  # noqa: F401,F403

DEBUG = False

# All default to True (secure-by-default). Set to False in .env only while
# running without a domain/TLS certificate yet (IP-only access) — flip back
# to True the moment HTTPS is in front of the site, or logins will silently
# stop working (browsers refuse to send "Secure" cookies over plain HTTP).
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)  # noqa: F405
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)  # noqa: F405

SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30 if SECURE_SSL_REDIRECT else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_SSL_REDIRECT

# nginx terminates TLS (once a certificate exists) and forwards this header —
# lets Django's request.is_secure() / SECURE_SSL_REDIRECT work behind the proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
