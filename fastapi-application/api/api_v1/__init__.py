from fastapi import APIRouter

from core.config import settings
from api.api_v1.users import users_router
from api.api_v1.cleanings import cleanings_router


router = APIRouter(
    prefix=settings.api.v1.prefix,
)
router.include_router(
    users_router,
    prefix=settings.api.v1.users,
)
router.include_router(
    cleanings_router,
    prefix=settings.api.v1.cleanings,
)
