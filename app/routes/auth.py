from datetime import timedelta

# We need to get templates from main or redefine.
# Redefining for modularity, but ideally should share instance.
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app import storage
from app.database import get_db
from app.models import UserCreate
from app.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    verify_password,
)

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["auth"])


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    email: str = Form(...),
    login: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_in = UserCreate(email=email, login=login, password=password)
        await storage.create_user(db, user_in)
        # Auto login or redirect to login? Redirect to login is simpler.
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    except ValueError as e:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": str(e)},
            status_code=400,
        )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    login: str = Form(...),  # can be email or login
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await storage.get_user_by_login_or_email(db, login)
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=400,
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response
