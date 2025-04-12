import logging

from pydantic import (
    BaseModel,
    field_validator,
)

logger = logging.getLogger(__name__)


class RequestSide(BaseModel):
    req_id: str
    method: str
    route: str
    ip: str
    url: str
    host: str | None
    body: str
    headers: dict

    @field_validator("body", mode="before")
    @classmethod
    def validate_body(cls, field: bytes) -> str:
        try:
            decoded = field.decode()
            return decoded
        except UnicodeDecodeError:
            logger.exception("Failed to decode the request body", exc_info=True)

        return ""


class ResponseSide(BaseModel):
    response_status_code: int
    response_size: int
    response_headers: dict
    response_body: str

    @field_validator("response_body", mode="before")
    @classmethod
    def validate_body(cls, field: bytes) -> str:
        try:
            decoded = field.decode()
            return decoded
        except UnicodeDecodeError:
            logger.exception("Failed to decode the response body", exc_info=True)

        return ""


class RequestLog(BaseModel):
    request: RequestSide
    response: ResponseSide
