from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import storage
from app.database import get_db
from app.deps import get_current_user
from app.models import User

router = APIRouter(tags=["favorites"])


@router.post("/favorites/{post_id}/add", response_class=RedirectResponse)
async def add_to_favorites(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Verify post exists
    post = await storage.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await storage.add_favorite(db, user.id, post_id)

    # Redirect back to referer or post detail
    referer = request.headers.get("referer")
    if referer:
        return RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url=f"/html/posts/{post_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/favorites/{post_id}/remove", response_class=RedirectResponse)
async def remove_from_favorites(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    await storage.remove_favorite(db, user.id, post_id)

    referer = request.headers.get("referer")
    if referer:
        return RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url=f"/html/posts/{post_id}", status_code=status.HTTP_303_SEE_OTHER)
