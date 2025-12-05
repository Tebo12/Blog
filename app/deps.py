from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app import storage
from app.database import get_db
from app.models import User
from app.security import decode_access_token


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None

    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    payload = decode_access_token(token)
    if payload is None:
        return None

    username: str | None = payload.get("sub")
    if username is None:
        return None

    try:
        user_id = int(username)
        user_orm = await storage.get_user(db, user_id)
        if user_orm:
            return User.model_validate(user_orm)
    except ValueError:
        pass

    return None
