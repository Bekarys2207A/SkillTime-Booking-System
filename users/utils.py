import uuid
import jwt
from datetime import datetime, timezone
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken


def now():
    return datetime.now(timezone.utc)


def make_access_token(user):
    return str(AccessToken.for_user(user))


def make_refresh_token():
    return uuid.uuid4().hex


def make_password_reset_token(user):
    payload = {
        "user_id": user.id,
        "action": "password_reset",
        "iat": int(now().timestamp()),
        "exp": int((now() + settings.JWT_RESET_TOKEN_LIFETIME).timestamp()),
        "nonce": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.JWT_RESET_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_reset_token(token):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_RESET_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload if payload.get("action") == "password_reset" else None
    except jwt.PyJWTError:
        return None