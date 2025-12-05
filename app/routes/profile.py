from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app import storage
from app.database import get_db
from app.deps import get_current_user
from app.models import User, UserUpdate

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["profile"])


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Fetch user's posts
    all_posts = await storage.list_posts(db)
    my_posts = [p for p in all_posts if p.author_id == user.id]

    # Fetch user's favorites
    my_favorites = await storage.list_favorites(db, user.id)

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user, "my_posts": my_posts, "my_favorites": my_favorites},
    )


@router.post("/profile", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    email: str = Form(...),
    login: str = Form(...),
    password: str = Form(None),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        update_data = UserUpdate(email=email, login=login)
        if password:
            update_data.password = password

        updated_user = await storage.update_user(db, user.id, update_data)

        # Re-fetch posts for template
        all_posts = await storage.list_posts(db)
        my_posts = [p for p in all_posts if p.author_id == updated_user.id]

        # Fetch user's favorites
        my_favorites = await storage.list_favorites(db, updated_user.id)

        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": updated_user,
                "my_posts": my_posts,
                "my_favorites": my_favorites,
                "success": "Profile updated successfully!",
            },
        )
    except ValueError as e:
        all_posts = await storage.list_posts(db)
        my_posts = [p for p in all_posts if p.author_id == user.id]
        my_favorites = await storage.list_favorites(db, user.id)
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": user,
                "my_posts": my_posts,
                "my_favorites": my_favorites,
                "error": str(e),
            },
            status_code=400,
        )
