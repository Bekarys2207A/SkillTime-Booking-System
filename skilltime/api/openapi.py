from drf_spectacular.types import OpenApiTypes

from skilltime.api.schema_serializers import ErrorResponseSerializer

COMMON_ERROR_RESPONSES = {
    400: ErrorResponseSerializer,
    401: ErrorResponseSerializer,
    403: ErrorResponseSerializer,
    404: ErrorResponseSerializer,
    429: ErrorResponseSerializer,
}

OK_OBJECT = OpenApiTypes.OBJECT