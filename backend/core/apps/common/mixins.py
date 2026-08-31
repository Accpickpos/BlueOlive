"""
Shared ViewSet mixins used across apps.
"""

from rest_framework.decorators import action
from rest_framework.response import Response


class LookupActionMixin:
    """
    Adds GET /{resource}/lookup/?search=&limit=&offset= — a lightweight,
    offset-paginated typeahead endpoint for search-as-you-type UIs
    (debtor/stock-item/creditor pickers, etc).

    Reuses whatever filter_backends/search_fields/filterset_class the
    ViewSet already declares (via self.filter_queryset) so search coverage
    here never drifts from the regular list endpoint — this swaps in a
    lighter serializer and simple offset/limit paging (rather than DRF's
    page-number pagination, which the frontend pickers don't speak) for
    dropdown rendering.

    Set `lookup_serializer_class` on the ViewSet to control the response
    shape; falls back to get_serializer_class() if not set.

    Response shape: {"results": [...], "count": <total matches>,
    "has_more": <bool>} — not a bare array, so frontend callers can page.
    """

    lookup_serializer_class = None
    lookup_limit_default = 20
    lookup_limit_max = 50

    @action(detail=False, methods=["get"])
    def lookup(self, request):
        try:
            limit = min(
                int(request.query_params.get("limit", self.lookup_limit_default)),
                self.lookup_limit_max,
            )
        except (TypeError, ValueError):
            limit = self.lookup_limit_default

        try:
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except (TypeError, ValueError):
            offset = 0

        queryset = self.filter_queryset(self.get_queryset())
        total = queryset.count()
        page = queryset[offset : offset + limit]

        serializer_class = self.lookup_serializer_class or self.get_serializer_class()
        serializer = serializer_class(
            page, many=True, context=self.get_serializer_context()
        )
        return Response(
            {
                "results": serializer.data,
                "count": total,
                "has_more": offset + limit < total,
            }
        )
