from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user

from . import storage
from .models import PostCreate, PostUpdate, User
from .routes.auth import router as auth_router
from .routes.favorites import router as favorites_router
from .routes.posts import router as posts_router
from .routes.profile import router as profile_router
from .routes.users import router as users_router

app = FastAPI(title="Simple Blog API")


app.include_router(users_router)
app.include_router(posts_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(favorites_router)


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    posts = await storage.list_posts(db, search_query=q)
    users = await storage.list_users(db)
    user_id_to_login: dict[int, str] = {u.id: u.login for u in users}
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "posts": posts,
            "user_id_to_login": user_id_to_login,
            "user": user,
            "search_query": q,
        },
    )


@app.get("/html/posts/new", response_class=HTMLResponse)
async def html_post_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> Response:
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "post_form.html",
        {"request": request, "mode": "create", "users": [user], "post": None, "user": user},
    )


@app.post("/html/posts/new", response_class=RedirectResponse)
async def html_post_new_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> Response:
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        post = PostCreate(title=title, content=content, author_id=user.id)
        created = await storage.create_post(db, post)
        return RedirectResponse(url=f"/html/posts/{created.id}", status_code=303)
    except ValueError as e:
        return templates.TemplateResponse(
            "post_form.html",
            {
                "request": request,
                "mode": "create",
                "users": [user],
                "post": None,
                "error": str(e),
                "user": user,
            },
            status_code=400,
        )


@app.get("/html/posts/{post_id}", response_class=HTMLResponse)
async def html_post_detail(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    post = await storage.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    author = await storage.get_user(db, post.author_id)

    is_fav = False
    if user:
        is_fav = await storage.is_favorited(db, user.id, post.id)

    return templates.TemplateResponse(
        "post_detail.html",
        {"request": request, "post": post, "author": author, "user": user, "is_favorited": is_fav},
    )


@app.get("/html/posts/{post_id}/edit", response_class=HTMLResponse)
async def html_post_edit(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> Response:
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    post = await storage.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    if post.author_id != user.id:
        return Response("Forbidden", status_code=403)

    return templates.TemplateResponse(
        "post_form.html",
        {"request": request, "mode": "edit", "users": [user], "post": post, "user": user},
    )


@app.post("/html/posts/{post_id}/edit", response_class=RedirectResponse)
async def html_post_edit_post(
    post_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> Response:
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    post = await storage.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    if post.author_id != user.id:
        return Response("Forbidden", status_code=403)

    try:
        await storage.update_post(db, post_id, PostUpdate(title=title, content=content))
        return RedirectResponse(url=f"/html/posts/{post_id}", status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
