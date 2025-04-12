from fastapi import Request


class RequestInfo:
    def __init__(self, request: Request) -> None:
        self.request = request

    @property
    def method(self) -> str:
        return self.request.method

    @property
    def route(self) -> str:
        return self.request.url.path

    @property
    def ip(self) -> str:
        if self.request.client is not None:
            return self.request.client.host
        return ""

    @property
    def url(self) -> str:
        return str(self.request.url)

    @property
    def host(self) -> str | None:
        return self.request.url.hostname

    @property
    def headers(self) -> dict:
        return {key: value for key, value in self.request.headers.items()}
