import logging
from types import MappingProxyType
from typing import (
    Any,
    override,
)

from fastapi.security import OAuth2PasswordBearer
from fastapi import (
    Request,
    HTTPException,
    status,
)
from jwt.exceptions import InvalidTokenError

from auth.utils.auth_utils import decode_jwt


logger = logging.getLogger(__name__)

SCOPES = MappingProxyType(
    {
        "read": "Permission to read information",
        "modify": "Permission to modify self information",
        "write": "Permission to edit information",
        "delete": "Permission to delete information",
    }
)


class TokenBearer(OAuth2PasswordBearer):
    """
    Subclass of OAuth2PasswordBearer.
    Overridden __call__ method, implemented json web token
    decoding and token type validation.
    """

    def __init__(
        self,
        token_type: str,
        tokenUrl: str = "/api/v1/auth/signin",
        scopes: MappingProxyType[str, str] = SCOPES,
        auto_error: bool = True,
    ) -> None:
        super().__init__(
            tokenUrl=tokenUrl,
            scopes=scopes,  # type: ignore
            auto_error=auto_error,
        )
        self._token_type = token_type

    @override
    async def __call__(self, request: Request) -> dict[str, Any]:
        token = await super().__call__(request=request)
        payload = self.get_current_token_payload(token=token)
        self.validate_token_type(
            payload=payload,
            token_type=self._token_type,
        )

        return payload

    @staticmethod
    def get_current_token_payload(token: str) -> dict[str, Any]:
        try:
            payload = decode_jwt(token=token)
        except InvalidTokenError:
            logger.exception("Failed to decode json web token", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials. Invalid token error or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    @staticmethod
    def validate_token_type(payload: dict[str, Any], token_type: str) -> None:
        current_token_type = payload.get("type")
        if current_token_type != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type {current_token_type!r} expected {token_type!r}",
                headers={"WWW-Authenticate": "Bearer"},
            )


access_token_bearer = TokenBearer(token_type="access")
refresh_token_bearer = TokenBearer(token_type="refresh")
