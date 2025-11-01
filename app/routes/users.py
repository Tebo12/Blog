from fastapi import APIRouter, HTTPException, status

from .. import storage
from ..models import User, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate) -> User:
    try:
        return await storage.create_user(user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/", response_model=list[User])
async def list_users() -> list[User]:
    return await storage.list_users()


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int) -> User:
    user = await storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user_in: UserUpdate) -> User:
    try:
        user = await storage.update_user(user_id, user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int) -> None:
    ok = await storage.delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="user not found")
    return None
