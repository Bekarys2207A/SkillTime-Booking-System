from __future__ import annotations
from typing import Any
from .models import AuditLog

SENSITIVE_KEYS = {"password", "access_token", "refresh_token", "token", "authorization"}

def _sanitize_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    if not meta:
        return {}
    clean = {}
    for k, v in meta.items():
        if isinstance(k, str) and k.lower() in SENSITIVE_KEYS:
            clean[k] = "***"
        else:
            clean[k] = v
    return clean

class AuditService:
    @staticmethod
    def log(*, actor, action: str, entity: str, entity_id: str | int, meta: dict | None = None) -> AuditLog:
        return AuditLog.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=action,
            entity=entity,
            entity_id=str(entity_id),
            meta=_sanitize_meta(meta),
        )