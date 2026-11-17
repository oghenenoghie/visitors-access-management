"""One error shape for every API failure (see documentation/api/api-architecture.md)."""

from rest_framework import exceptions, status
from rest_framework.views import exception_handler

_STATUS_CODES = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "not_authenticated",
    status.HTTP_403_FORBIDDEN: "permission_denied",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_429_TOO_MANY_REQUESTS: "throttled",
}


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, exceptions.ValidationError):
        code, message, details = "validation_error", "Request validation failed.", response.data
    else:
        data = response.data
        message = str(data.get("detail", "")) if isinstance(data, dict) else str(data)
        details = {}
        codes = exc.get_codes() if isinstance(exc, exceptions.APIException) else None
        code = codes if isinstance(codes, str) else _STATUS_CODES.get(response.status_code, "error")

    response.data = {"error": {"code": code, "message": message, "details": details}}
    return response
