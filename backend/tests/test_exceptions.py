from rest_framework import exceptions

from apps.common.exceptions import api_exception_handler


def test_validation_errors_carry_field_details(db):
    response = api_exception_handler(exceptions.ValidationError({"email": ["Required."]}), {})
    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
    assert response.data["error"]["details"] == {"email": ["Required."]}


def test_permission_denied_uses_the_standard_shape(db):
    response = api_exception_handler(exceptions.PermissionDenied(), {})
    assert response.status_code == 403
    assert response.data["error"]["code"] == "permission_denied"


def test_unhandled_exceptions_are_left_to_django():
    assert api_exception_handler(RuntimeError("boom"), {}) is None
