from fastapi import APIRouter


router = APIRouter(
    tags=["Users"],
)


@router.get("")
def greeting():
    return {"message": "Hello user!"}
