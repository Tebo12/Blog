from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from .. import storage
from ..models import Post, PostCreate, PostUpdate

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(post_in: PostCreate, db: AsyncSession = Depends(get_db)) -> Post:
    try:
        return await storage.create_post(db, post_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/", response_model=list[Post])
async def list_posts(
    authorId: int | None = Query(default=None, alias="authorId"), db: AsyncSession = Depends(get_db)
) -> list[Post]:
    # TODO: Update storage.list_posts to support filtering
    return await storage.list_posts(db)


@router.get("/{post_id}", response_model=Post)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)) -> Post:
    post = await storage.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    return post


@router.put("/{post_id}", response_model=Post)
async def update_post(post_id: int, post_in: PostUpdate, db: AsyncSession = Depends(get_db)) -> Post:
    try:
        post = await storage.update_post(db, post_id, post_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return post


# TODO: Add delete_post to storage.py
