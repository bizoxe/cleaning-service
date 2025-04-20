from collections.abc import Awaitable
from typing import Any

from async_typer import AsyncTyper

from scripts.init_roles_and_admin import (
    create_admin_and_editor,
    seed_roles_and_permissions,
)

async_typer = AsyncTyper()


async def chain(*awaitables: Awaitable[Any]) -> list[Any]:
    return [await a for a in awaitables]


@async_typer.async_command()  # type: ignore
async def seed() -> None:
    await chain(
        seed_roles_and_permissions(),
        create_admin_and_editor(),
    )


if __name__ == "__main__":
    async_typer()
