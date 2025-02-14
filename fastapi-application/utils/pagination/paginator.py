"""
Cursor-based pagination.
See: https://github.com/lewoudar/fastapi-paginator
"""

from typing import (
    TypeVar,
    Generic,
    Any,
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select

from core.models import Base
from server.utils.middlewares import request_object
from utils.pagination.helpers import (
    encode_id,
    decode_id,
)
from utils.pagination.schemas import ItemQueryParams


ORMModel = TypeVar("ORMModel", bound=Base)
ItemQueryParamsType = TypeVar("ItemQueryParamsType", bound=ItemQueryParams)


class Paginator(Generic[ORMModel]):
    def __init__(
        self,
        session: AsyncSession,
        model: type[ORMModel],
        query: Select,
        max_results: int,
        cursor: str | None,
        params: ItemQueryParamsType,
    ) -> None:
        self.session = session
        self._model: type[ORMModel] = model
        self.query = query
        self.max_results = max_results
        self.cursor = cursor
        self.request = request_object.get()
        self.next_cursor: str | None = None
        self.previous_cursor: str | None = None
        self.params = params

    async def _get_next_model_objects(self, query: Select) -> list[ORMModel]:
        initial_m_objects = [item for item in await self.session.scalars(query)]
        if len(initial_m_objects) < self.max_results + 1:
            return initial_m_objects
        else:
            model_objects = initial_m_objects[:-1]
            self.next_cursor = encode_id(model_objects[-1].id)
            return model_objects

    async def get_response(self) -> dict[str, Any]:
        if self.cursor is None:
            query = self.query.limit(self.max_results + 1)
        else:
            ident = decode_id(self.cursor)
            query = self.query.where(self._model.id > ident).limit(self.max_results + 1)
        model_objects = await self._get_next_model_objects(query=query)

        if self.params.sort_by:
            model_objects = self.get_sorted_model_objects(
                objects=model_objects, params=self.params
            )
        return {
            "count": len(model_objects),
            "previous_page": await self._get_previous_page(),
            "next_page": self._get_next_page(),
            "previous_cursor": self.previous_cursor,
            "next_cursor": self.next_cursor,
            "items": model_objects,
        }

    def _get_url(self, cursor: str) -> str:
        url = self.request.url

        return f"{url.scheme}://{url.netloc}{url.path}?max_results={self.max_results}&cursor={cursor}"

    def _get_next_page(self) -> str | None:
        if self.next_cursor is None:
            return None
        return self._get_url(cursor=self.next_cursor)

    async def _get_previous_model_objects(
        self, last_model_obj_id: int
    ) -> list[ORMModel]:
        query = (
            self.query.where(self._model.id < last_model_obj_id)
            .order_by(self._model.id.desc())
            .limit(self.max_results)
        )
        model_objects = [item for item in await self.session.scalars(query)]

        return model_objects

    async def _get_first_model_obj(self) -> ORMModel | None:
        res = await self.session.scalars(self.query)

        return res.first()

    async def _get_previous_url(self, model_objects: list[ORMModel]) -> str | None:
        if not model_objects:
            return None

        cursor_model_obj_id = model_objects[-1].id
        first_model_obj = await self._get_first_model_obj()
        if first_model_obj.id == cursor_model_obj_id:
            cursor_model_obj_id -= 1
        self.previous_cursor = encode_id(cursor_model_obj_id)

        return self._get_url(cursor=self.previous_cursor)

    async def _get_previous_page(self) -> str | None:
        if self.cursor is None:
            return None
        else:
            last_model_obj_id = decode_id(self.cursor)
            previous_model_objects = await self._get_previous_model_objects(
                last_model_obj_id
            )

            return await self._get_previous_url(previous_model_objects)

    @staticmethod
    def get_sorted_model_objects(
        objects: list[ORMModel], params: ItemQueryParamsType
    ) -> list[ORMModel]:
        sorted_objects = sorted(
            objects,
            key=lambda obj: getattr(obj, params.sort_by),
            reverse=params.descending,
        )
        return sorted_objects


async def paginate(
    session: AsyncSession,
    model: type[ORMModel],
    query: Select,
    max_results: int,
    cursor: str | None,
    params: ItemQueryParamsType,
) -> dict[str, Any]:
    paginator = Paginator(
        session=session,
        model=model,
        query=query,
        max_results=max_results,
        cursor=cursor,
        params=params,
    )

    return await paginator.get_response()
