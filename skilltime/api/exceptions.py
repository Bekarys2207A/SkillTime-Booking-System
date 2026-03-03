from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError,
    PermissionDenied,
    NotFound,
    AuthenticationFailed,
    NotAuthenticated,
    Throttled,
)


def custom_exception_handler(exc, context):
    """
    Единый формат ошибок:
    { "code": "...", "message": "...", "details": ... }
    """
    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {"code": "internal_error", "message": "Internal server error", "details": None},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = "error"
    message = "Request failed"
    details = response.data

    if isinstance(exc, ValidationError):
        code = "validation_error"
        message = "Validation failed"
    elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        code = "auth_failed"
        message = "Authentication failed"
    elif isinstance(exc, PermissionDenied):
        code = "permission_denied"
        message = "Permission denied"
    elif isinstance(exc, NotFound):
        code = "not_found"
        message = "Not found"
    elif isinstance(exc, Throttled):
        code = "throttled"
        message = "Too many requests"

    response.data = {"code": code, "message": message, "details": details}
    return response