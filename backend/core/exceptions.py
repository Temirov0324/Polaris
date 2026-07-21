from rest_framework.views import exception_handler


def _flatten_message(detail):
    if isinstance(detail, (list, tuple)):
        return " ".join(str(_flatten_message(item)) for item in detail)
    if isinstance(detail, dict):
        return " ".join(f"{key}: {_flatten_message(value)}" for key, value in detail.items())
    return str(detail)


def envelope_exception_handler(exc, context):
    """Reshapes DRF's default error response into the project-wide
    {"error": {"code", "message_uz", "details"}} envelope."""
    response = exception_handler(exc, context)
    if response is None:
        return None

    code = getattr(exc, "default_code", exc.__class__.__name__)
    message = _flatten_message(response.data)

    response.data = {
        "error": {
            "code": code,
            "message_uz": message,
            "details": response.data,
        }
    }
    return response
