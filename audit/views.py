from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from .models import AuditLog
from .serializers import AuditLogSerializer
from .permissions import IsAdminRole

# Create your views here.

class AuditLogListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminRole]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.all()

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


class AuditLogDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsAdminRole]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()