from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from .. import storage
from ..models import User, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    try:
        return await storage.create_user(db, user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/", response_model=list[User])
async def list_users(db: AsyncSession = Depends(get_db)) -> list[User]:
    return await storage.list_users(db)


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> User:
    user = await storage.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user_in: UserUpdate, db: AsyncSession = Depends(get_db)) -> User:
    try:
        user = await storage.update_user(db, user_id, user_in)
    except ValueError as e:
        # could be not found or duplicate
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    return user


# TODO: Add delete_user to storage.py
