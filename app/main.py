from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .routes.users import router as users_router
from .routes.posts import router as posts_router
from . import storage
from .models import PostCreate, PostUpdate


app = FastAPI(title="Simple Blog API")


app.include_router(users_router)
app.include_router(posts_router)


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.on_event("startup")
async def _startup() -> None:
    await storage.load_data()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await storage.save_data()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    posts = await storage.list_posts()
    users = await storage.list_users()
    user_id_to_login: Dict[int, str] = {u.id: u.login for u in users}
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "posts": posts,
            "user_id_to_login": user_id_to_login,
        },
    )


@app.get("/html/posts/new", response_class=HTMLResponse)
async def html_post_new(request: Request) -> HTMLResponse:
    users = await storage.list_users()
    return templates.TemplateResponse(
        "post_form.html",
        {"request": request, "mode": "create", "users": users, "post": None},
    )


@app.post("/html/posts/new", response_class=RedirectResponse)
async def html_post_new_post(
    request: Request, title: str = Form(...), content: str = Form(...), authorId: int = Form(...)
) -> RedirectResponse:
    try:
        post = PostCreate(title=title, content=content, authorId=authorId)
        created = await storage.create_post(post)
        return RedirectResponse(url=f"/html/posts/{created.id}", status_code=303)
    except ValueError as e:
        users = await storage.list_users()
        return templates.TemplateResponse(
            "post_form.html",
            {"request": request, "mode": "create", "users": users, "post": None, "error": str(e)},
            status_code=400,
        )


@app.get("/html/posts/{post_id}", response_class=HTMLResponse)
async def html_post_detail(post_id: int, request: Request) -> HTMLResponse:
    post = await storage.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    author = await storage.get_user(post.authorId)
    return templates.TemplateResponse(
        "post_detail.html",
        {"request": request, "post": post, "author": author},
    )


@app.get("/html/posts/{post_id}/edit", response_class=HTMLResponse)
async def html_post_edit(post_id: int, request: Request) -> HTMLResponse:
    post = await storage.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    users = await storage.list_users()
    return templates.TemplateResponse(
        "post_form.html",
        {"request": request, "mode": "edit", "users": users, "post": post},
    )


@app.post("/html/posts/{post_id}/edit", response_class=RedirectResponse)
async def html_post_edit_post(
    post_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
) -> RedirectResponse:
    updated = await storage.update_post(post_id, PostUpdate(title=title, content=content))
    if not updated:
        raise HTTPException(status_code=404, detail="post not found")
    return RedirectResponse(url=f"/html/posts/{post_id}", status_code=303)
