"""
Common App Views
AccessGrantViewSet — the role x module x function_type permission matrix
(manual §8.1 Password Maintenance foundation). List + bulk_update only; no
per-row create/delete since the full matrix is seeded once by migration and
every (role, module, function_type) combination should always exist.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AccessGrant
from .serializers import AccessGrantBulkUpdateSerializer, AccessGrantSerializer


class AccessGrantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List: GET /api/common/access-grants/
    Bulk update: POST /api/common/access-grants/bulk_update/
    """

    queryset = AccessGrant.objects.all()
    serializer_class = AccessGrantSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["role", "module", "function_type", "is_allowed"]

    @action(detail=False, methods=["post"])
    def bulk_update(self, request):
        """
        Body: {"grants": [{"role": "...", "module": "...", "function_type": "...", "is_allowed": true}, ...]}
        Updates only rows that already exist (the matrix is fully seeded by
        migration) — never creates new (role, module, function_type) rows
        from arbitrary client input.
        """
        grants_data = request.data.get("grants", [])
        serializer = AccessGrantBulkUpdateSerializer(data=grants_data, many=True)
        serializer.is_valid(raise_exception=True)

        updated = 0
        missing = []
        for cell in serializer.validated_data:
            count = AccessGrant.objects.filter(
                role=cell["role"], module=cell["module"], function_type=cell["function_type"]
            ).update(is_allowed=cell["is_allowed"])
            if count:
                updated += count
            else:
                missing.append(cell)

        return Response(
            {"updated": updated, "missing": missing},
            status=status.HTTP_200_OK if not missing else status.HTTP_207_MULTI_STATUS,
        )
