from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import tables
from app.models import PostCreate, PostUpdate, UserCreate, UserUpdate
from app.security import get_password_hash


async def create_user(session: AsyncSession, payload: UserCreate) -> tables.User:
    stmt = select(tables.User).where((tables.User.email == payload.email) | (tables.User.login == payload.login))
    result = await session.execute(stmt)
    if result.scalars().first():
        raise ValueError("email or login already exists")

    hashed_pw = get_password_hash(payload.password)
    user = tables.User(
        email=payload.email,
        login=payload.login,
        password_hash=hashed_pw,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, user_id: int) -> tables.User | None:
    return await session.get(tables.User, user_id)


async def get_user_by_login_or_email(session: AsyncSession, login_str: str) -> tables.User | None:
    stmt = select(tables.User).where(or_(tables.User.email == login_str, tables.User.login == login_str))
    result = await session.execute(stmt)
    return result.scalars().first()


async def list_users(session: AsyncSession) -> list[tables.User]:
    stmt = select(tables.User).order_by(tables.User.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_user(session: AsyncSession, user_id: int, payload: UserUpdate) -> tables.User:
    user = await get_user(session, user_id)
    if not user:
        raise ValueError("user not found")

    if payload.email is not None:
        stmt = select(tables.User).where(tables.User.email == payload.email, tables.User.id != user_id)
        if (await session.execute(stmt)).scalars().first():
            raise ValueError("email already exists")
        user.email = payload.email

    if payload.login is not None:
        stmt = select(tables.User).where(tables.User.login == payload.login, tables.User.id != user_id)
        if (await session.execute(stmt)).scalars().first():
            raise ValueError("login already exists")
        user.login = payload.login

    if payload.password is not None:
        user.password_hash = get_password_hash(payload.password)

    await session.commit()
    await session.refresh(user)
    return user


async def create_post(session: AsyncSession, payload: PostCreate) -> tables.Post:
    author = await get_user(session, payload.author_id)
    if not author:
        raise ValueError("author does not exist")

    post = tables.Post(
        author_id=payload.author_id,
        title=payload.title,
        content=payload.content,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


async def get_post(session: AsyncSession, post_id: int) -> tables.Post | None:
    return await session.get(tables.Post, post_id)


async def list_posts(session: AsyncSession, search_query: str | None = None) -> list[tables.Post]:
    stmt = select(tables.Post).order_by(tables.Post.created_at.desc())

    if search_query:
        term = f"%{search_query}%"
        stmt = stmt.where(or_(tables.Post.title.ilike(term), tables.Post.content.ilike(term)))

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_post(session: AsyncSession, post_id: int, payload: PostUpdate) -> tables.Post:
    post = await get_post(session, post_id)
    if not post:
        raise ValueError("post not found")

    if payload.title is not None:
        post.title = payload.title
    if payload.content is not None:
        post.content = payload.content

    await session.commit()
    await session.refresh(post)
    return post


async def add_favorite(session: AsyncSession, user_id: int, post_id: int) -> None:
    stmt = select(tables.Favorite).where(tables.Favorite.user_id == user_id, tables.Favorite.post_id == post_id)
    if (await session.execute(stmt)).scalars().first():
        return

    fav = tables.Favorite(user_id=user_id, post_id=post_id)
    session.add(fav)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def remove_favorite(session: AsyncSession, user_id: int, post_id: int) -> None:
    stmt = delete(tables.Favorite).where(tables.Favorite.user_id == user_id, tables.Favorite.post_id == post_id)
    await session.execute(stmt)
    await session.commit()


async def is_favorited(session: AsyncSession, user_id: int, post_id: int) -> bool:
    stmt = select(tables.Favorite).where(tables.Favorite.user_id == user_id, tables.Favorite.post_id == post_id)
    result = await session.execute(stmt)
    return result.scalars().first() is not None


async def list_favorites(session: AsyncSession, user_id: int) -> list[tables.Post]:
    stmt = (
        select(tables.Post)
        .join(tables.Favorite, tables.Favorite.post_id == tables.Post.id)
        .where(tables.Favorite.user_id == user_id)
        .order_by(tables.Favorite.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
