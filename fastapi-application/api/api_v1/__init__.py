__all__ = ("router",)

from fastapi import APIRouter

from api.api_v1.cleanings import cleanings_router
from api.api_v1.evaluations import evaluations_router
from api.api_v1.offers import (
    offers_cleanings_router,
    offers_router,
)
from api.api_v1.profiles import profiles_router
from api.api_v1.users import (
    auth_router,
    users_router,
)
from core.config import settings

router = APIRouter(
    prefix=settings.api.v1.prefix,
)
router.include_router(
    auth_router,
    prefix=settings.api.v1.auth,
)
router.include_router(
    users_router,
    prefix=settings.api.v1.users,
)
router.include_router(
    cleanings_router,
    prefix=settings.api.v1.cleanings,
)
router.include_router(
    profiles_router,
    prefix=settings.api.v1.profiles,
)
router.include_router(
    offers_router,
    prefix=settings.api.v1.offers,
)
router.include_router(
    offers_cleanings_router,
    prefix=settings.api.v1.offers_cleanings,
)
router.include_router(
    evaluations_router,
    prefix=settings.api.v1.evaluations,
)
