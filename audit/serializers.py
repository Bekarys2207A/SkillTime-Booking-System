from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = ["id", "ts", "action", "entity", "entity_id", "meta", "actor", "actor_email"]

    def get_actor_email(self, obj) -> str | None:
        return getattr(obj.actor, "email", None)