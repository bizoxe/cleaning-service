from fastapi import APIRouter

router = APIRouter(
    tags=["Cleanings"],
)


@router.get("")
def get_cleanings():
    return {"message": "Hello cleanings!"}
