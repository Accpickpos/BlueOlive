"""
Shared ViewSet mixins used across apps.
"""

from rest_framework.decorators import action
from rest_framework.response import Response


class ModuleFunctionPermissionMixin:
    """
    Adds a HasModuleFunctionAccess check (apps.common.models.AccessGrant,
    manual §8.1 Password Maintenance) on top of whatever permission_classes
    a ViewSet already declares. This is the module-by-module rollout of
    that permission system — set `access_module` to one of
    AccessGrant.MODULE_CHOICES on the ViewSet to opt in.

    The action -> function_type mapping is a generic default covering
    standard ModelViewSet actions plus a name-based heuristic for custom
    @action methods, so most ViewSets need zero extra configuration.
    Override `action_function_types = {"my_action": "REPORT"}` on a
    subclass for the cases the heuristic gets wrong — do this deliberately,
    not defensively, since a wrong mapping either over-restricts a
    legitimate action or under-restricts a sensitive one.
    """

    access_module = None  # e.g. "cash_book" — set on the ViewSet subclass

    DEFAULT_ACTION_FUNCTION_TYPES = {
        "list": "ENQUIRY",
        "retrieve": "ENQUIRY",
        "create": "TRANSACTIONS",
        "update": "TRANSACTIONS",
        "partial_update": "TRANSACTIONS",
        "destroy": "MAINTENANCE",
    }

    # Explicit per-ViewSet overrides for custom @action methods.
    action_function_types: dict[str, str] = {}

    # Heuristic for custom @action names not explicitly mapped. Checked in
    # order; first match wins. Defaults to ENQUIRY (least disruptive) if
    # nothing matches, rather than silently blocking an unmapped action.
    _NAME_HEURISTICS = (
        (("report", "summary", "analysis", "statement", "enquiry"), "REPORT"),
        (
            (
                "delete",
                "deactivate",
                "activate",
                "void",
                "cancel",
                "clear",
                "reset",
                "set_default",
                "adjust",
                "archive",
            ),
            "MAINTENANCE",
        ),
        (
            (
                "post",
                "approve",
                "reconcile",
                "allocate",
                "receive",
                "issue",
                "pay",
                "run_",
                "convert",
            ),
            "TRANSACTIONS",
        ),
    )

    def get_function_type(self):
        current_action = getattr(self, "action", None) or ""
        if current_action in self.action_function_types:
            return self.action_function_types[current_action]
        if current_action in self.DEFAULT_ACTION_FUNCTION_TYPES:
            return self.DEFAULT_ACTION_FUNCTION_TYPES[current_action]

        name = current_action.lower()
        for keywords, function_type in self._NAME_HEURISTICS:
            if any(keyword in name for keyword in keywords):
                return function_type

        # No keyword match: fall back by HTTP method rather than a single
        # fixed default. A custom @action GET endpoint that doesn't match
        # any keyword (e.g. a bespoke lookup) is almost always safe to
        # treat as ENQUIRY; a custom mutating endpoint (POST/PUT/PATCH/
        # DELETE) that doesn't match any keyword is exactly the case this
        # mixin can't classify confidently, so it defaults to the more
        # restrictive MAINTENANCE rather than silently under-restricting an
        # unreviewed state-changing action.
        request = getattr(self, "request", None)
        method = getattr(request, "method", "GET")
        if method in ("GET", "HEAD", "OPTIONS"):
            return "ENQUIRY"
        return "MAINTENANCE"

    def check_permissions(self, request):
        """
        Hooks check_permissions rather than get_permissions: several
        ViewSets in this codebase already override get_permissions()
        directly (e.g. a SAFE_METHODS-based read/write split) — since that
        method is defined directly on the concrete ViewSet class, it wins
        Python's normal method resolution over this mixin's version even
        with the mixin listed first in the bases, silently skipping this
        check entirely. check_permissions() is not overridden anywhere in
        this codebase, so layering the module x function check there
        always runs, as an additional gate on top of whatever permission
        logic (custom or default) the ViewSet already has, regardless of
        which one it uses.
        """
        super().check_permissions(request)
        if self.access_module:
            from apps.common.permissions import HasModuleFunctionAccess

            permission = HasModuleFunctionAccess(
                self.access_module, self.get_function_type()
            )
            if not permission.has_permission(request, self):
                self.permission_denied(
                    request,
                    message="You do not have access to this module/function for your role.",
                    code="access_grant_denied",
                )


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
