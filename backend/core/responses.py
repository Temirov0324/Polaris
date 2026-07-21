from rest_framework.response import Response


def envelope(data, meta=None, status=200):
    body = {"data": data}
    if meta is not None:
        body["meta"] = meta
    return Response(body, status=status)
