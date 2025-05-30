import logging
from math import ceil
from time import time
from uuid import uuid4

from fastapi import (
    Request,
    Response,
)
from starlette.background import BackgroundTask
from starlette.middleware.base import RequestResponseEndpoint

from utils.custom_logger.helpers import RequestInfo
from utils.custom_logger.schemas import (
    RequestLog,
    RequestSide,
    ResponseSide,
)

PASS_ROUTES = {
    "/openapi.json",
    "/docs",
}

logger = logging.getLogger("main")


class LoggingMiddleware:
    async def __call__(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
        *args,
        **kwargs,
    ) -> Response:
        req_id = str(uuid4())
        exc_obj = None
        start_time = time()
        try:
            request.state.req_id = req_id
            request.state.body = await request.body()
            response = await call_next(request)
        except Exception as ex:
            response = Response(
                content=bytes("Internal Server Error".encode()),
                status_code=500,
            )
            exc_obj = ex
        else:
            if request.url.path in PASS_ROUTES:
                return response
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            resp_body = b"".join(chunks)

            task = BackgroundTask(
                func=self.log_request,
                request=request,
                response=response,
                response_body=resp_body,
                exception_ibj=exc_obj,
                start_time=start_time,
            )
            response = Response(
                content=resp_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
                background=task,
            )

        return response

    @staticmethod
    def log_request(
        request: Request,
        response: Response,
        response_body: bytes,
        exception_ibj: BaseException | None,
        start_time: float,
    ) -> None:
        request_info = RequestInfo(request)
        request_log = RequestLog(
            request=RequestSide(
                req_id=request.state.req_id,
                body=request.state.body,
                method=request_info.method,
                route=request_info.route,
                ip=request_info.ip,
                url=request_info.url,
                host=request_info.host,
                headers=request_info.headers,
            ),
            response=ResponseSide(
                response_status_code=response.status_code,
                response_size=int(response.headers.get("content-length", 0)),
                response_headers=dict(response.headers.items()),
                response_body=response_body,
            ),
        )
        duration: int = ceil((time() - start_time) * 1000)
        logger.log(
            level=20 if exception_ibj is None else 40,
            msg="status code=%s method=%s requested url=%s duration ms=%s"
            % (
                response.status_code,
                request.method,
                request.url,
                duration,
            ),
            extra={**request_log.model_dump()},
            exc_info=exception_ibj,
        )
