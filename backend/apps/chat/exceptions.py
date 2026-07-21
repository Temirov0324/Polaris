from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_429_TOO_MANY_REQUESTS


class ChatRateLimitExceeded(APIException):
    status_code = HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Kunlik xabar limitiga yetdingiz (30 ta). Ertaga qayta urinib ko'ring."
    default_code = "rate_limited"
