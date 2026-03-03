from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from .models import AuditLog
from .serializers import AuditLogSerializer
from .permissions import IsAdminRole

from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from skilltime.api.schema_serializers import ErrorResponseSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["Audit"],
        summary="List audit logs (admin)",
        description="Admin-only endpoint for searching audit logs.",
        parameters=[
            OpenApiParameter(name="entity", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="entity_id", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="actor_id", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="action", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="limit", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="offset", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False),
        ],
        responses={200: AuditLogSerializer(many=True), 403: ErrorResponseSerializer},
    )
)
class AuditLogListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminRole]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()

        entity = self.request.query_params.get("entity")
        entity_id = self.request.query_params.get("entity_id")
        actor_id = self.request.query_params.get("actor_id")
        action = self.request.query_params.get("action")

        if entity:
            qs = qs.filter(entity=entity)
        if entity_id:
            qs = qs.filter(entity_id=str(entity_id))
        if actor_id:
            qs = qs.filter(actor_id=actor_id)
        if action:
            qs = qs.filter(action=action)

        return qs


@extend_schema_view(
    get=extend_schema(
        tags=["Audit"],
        summary="Get audit log detail (admin)",
        responses={200: AuditLogSerializer, 403: ErrorResponseSerializer, 404: ErrorResponseSerializer},
    )
)
class AuditLogDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsAdminRole]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()