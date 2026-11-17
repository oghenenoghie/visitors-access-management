import pyotp

from apps.common.crypto import decrypt

URL_LOGIN = "/api/v1/auth/login/"


def login(client, email, password, **extra):
    return client.post(URL_LOGIN, {"email": email, "password": password}, format="json", **extra)


def code_at(user, timestamp):
    """The TOTP code valid at ``timestamp`` for the user's enrolled (or pending) device."""
    secret = decrypt(user.totp_device.secret_encrypted)
    return pyotp.TOTP(secret).at(timestamp)
