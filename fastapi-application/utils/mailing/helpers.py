import logging

from itsdangerous import (
    BadSignature,
    URLSafeSerializer,
)

from core.config import settings

logger = logging.getLogger(__name__)

serializer = URLSafeSerializer(
    secret_key=settings.mailing_cfg.secret_key,
    salt=settings.mailing_cfg.salt,
)


def create_url_safe_token(email: str) -> str:
    _token = serializer.dumps(email)

    return _token


def decode_url_safe_token(token: str) -> dict[str, str] | None:
    try:
        email = serializer.loads(token)
    except BadSignature:
        logger.exception(
            "Verification of the email token signature failed",
            exc_info=True,
        )
        return None

    return {"email": email}
