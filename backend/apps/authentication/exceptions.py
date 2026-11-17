from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidCredentials(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "invalid_credentials"
    default_detail = "Invalid email or password."


class InvalidChallenge(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "invalid_challenge"
    default_detail = "The sign-in session has expired. Sign in again."


class InvalidTwoFactorCode(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "invalid_two_factor_code"
    default_detail = "The verification code is invalid."


class InvalidResetCode(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "invalid_reset_code"
    default_detail = "The reset code is invalid or has expired."


class TwoFactorState(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "two_factor_state"
    default_detail = "Two-factor authentication is not in the required state."
