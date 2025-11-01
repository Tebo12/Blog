from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from ..models import Post, PostCreate, PostUpdate
from .. import storage


router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(post_in: PostCreate) -> Post:
    try:
        return await storage.create_post(post_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[Post])
async def list_posts(authorId: Optional[int] = Query(default=None)) -> List[Post]:
    return await storage.list_posts(author_id=authorId)


@router.get("/{post_id}", response_model=Post)
async def get_post(post_id: int) -> Post:
    post = await storage.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    return post


@router.put("/{post_id}", response_model=Post)
async def update_post(post_id: int, post_in: PostUpdate) -> Post:
    post = await storage.update_post(post_id, post_in)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int) -> None:
    ok = await storage.delete_post(post_id)
    if not ok:
        raise HTTPException(status_code=404, detail="post not found")
    return None
