from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """Reads the access token from an httpOnly cookie instead of the
    Authorization header, so the frontend never touches the raw JWT
    (mitigates XSS token theft). Falls back to the header for tooling
    such as the Swagger UI "Authorize" button."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)
        if raw_token is None:
            return super().authenticate(request)

        validated_token = self.get_validated_token(raw_token)
        try:
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            return None
