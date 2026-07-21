from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class EnvelopePagination(LimitOffsetPagination):
    """Paginates and wraps the list response in the project-wide
    {"data": ..., "meta": ...} envelope."""

    default_limit = 20
    max_limit = 100

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("data", data),
                    (
                        "meta",
                        OrderedDict(
                            [
                                ("count", self.count),
                                ("limit", self.limit),
                                ("offset", self.offset),
                                ("next", self.get_next_link()),
                                ("previous", self.get_previous_link()),
                            ]
                        ),
                    ),
                ]
            )
        )
