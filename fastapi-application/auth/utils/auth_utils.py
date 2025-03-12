"""
This module contains auxiliary functions for user authentication.
"""

import uuid
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from typing import Any

import bcrypt
import jwt

from core.config import settings


def encode_jwt(
    payload: dict[str, Any],
    private_key: str = settings.auth_jwt.private_key_path.read_text(),  # noqa: B008
    algorithm: str = settings.auth_jwt.algorithm,
    expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
    expire_timedelta: timedelta | None = None,
) -> str:
    """
    Is used as a base function to issue json web tokens.
    Args:
        payload: User information.
        private_key: Private key generated via openssl.
        algorithm: The RS256 algorithm is used.
        expire_minutes: Token lifetime.
        expire_timedelta: Refresh token lifetime by default None.
    """
    to_encode = payload.copy()
    time_now = datetime.now(timezone.utc)
    if expire_timedelta:
        expire = time_now + expire_timedelta
    else:
        expire = time_now + timedelta(minutes=expire_minutes)

    to_encode.update(
        jti=str(uuid.uuid4()),
        iat=time_now,
        exp=expire,
    )

    return jwt.encode(
        payload=to_encode,
        key=private_key,
        algorithm=algorithm,
    )


def decode_jwt(
    token: str | bytes,
    public_key: str = settings.auth_jwt.public_key_path.read_text(),  # noqa: B008
    algorithm: str = settings.auth_jwt.algorithm,
) -> dict[str, Any]:
    """
    Decodes JWT.
    Args:
        token: Json web token.
        public_key: Public key generated via openssl.
        algorithm: The RS256 algorithm is used.
    """

    return jwt.decode(
        jwt=token,
        key=public_key,
        algorithms=[algorithm],
    )


def hash_password(*, plaintext_password: str) -> bytes:
    """
    Generates a password hash value.
    Args:
        plaintext_password: The password to be hashed.

    Returns:
      bytes: The hash value of the password.
    """
    salt = bcrypt.gensalt()
    pwd_bytes: bytes = plaintext_password.encode()

    return bcrypt.hashpw(
        password=pwd_bytes,
        salt=salt,
    )


def verify_password(
    *,
    plaintext_password: str,
    hashed_password: bytes,
) -> bool:
    """
    Verify if a plain password matches a hashed password.
    Args:
        plaintext_password: A plain password that needs to be verified.
        hashed_password: A hashed password for comparison purposes.

    Returns:
            True if the plain password matches the hashed password, False otherwise.
    """
    pwd_bytes: bytes = plaintext_password.encode()

    return bcrypt.checkpw(
        password=pwd_bytes,
        hashed_password=hashed_password,
    )
