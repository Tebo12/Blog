import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import ValidationError

from .models import User, UserCreate, UserUpdate, Post, PostCreate, PostUpdate


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
POSTS_FILE = DATA_DIR / "posts.json"


_user_id_to_user: Dict[int, User] = {}
_post_id_to_post: Dict[int, Post] = {}
_next_user_id: int = 1
_next_post_id: int = 1


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def create_user(payload: UserCreate) -> User:
    global _next_user_id
    for user in _user_id_to_user.values():
        if user.email == payload.email:
            raise ValueError("email already exists")
        if user.login == payload.login:
            raise ValueError("login already exists")
    user = User(
        id=_next_user_id,
        email=payload.email,
        login=payload.login,
        password=payload.password,
        createdAt=_utcnow(),
        updatedAt=_utcnow(),
    )
    _user_id_to_user[user.id] = user
    _next_user_id += 1
    return user


async def list_users() -> List[User]:
    return list(sorted(_user_id_to_user.values(), key=lambda u: u.id))


async def get_user(user_id: int) -> Optional[User]:
    return _user_id_to_user.get(user_id)


async def update_user(user_id: int, changes: UserUpdate) -> Optional[User]:
    user = _user_id_to_user.get(user_id)
    if user is None:
        return None
    if changes.email is not None and changes.email != user.email:
        for other in _user_id_to_user.values():
            if other.email == changes.email and other.id != user_id:
                raise ValueError("email already exists")
        user.email = changes.email
    if changes.login is not None and changes.login != user.login:
        for other in _user_id_to_user.values():
            if other.login == changes.login and other.id != user_id:
                raise ValueError("login already exists")
        user.login = changes.login
    if changes.password is not None:
        user.password = changes.password
    user.updatedAt = _utcnow()
    _user_id_to_user[user_id] = user
    return user


async def delete_user(user_id: int) -> bool:
    if user_id in _user_id_to_user:
        del _user_id_to_user[user_id]
        return True
    return False


async def create_post(payload: PostCreate) -> Post:
    global _next_post_id
    if payload.authorId not in _user_id_to_user:
        raise ValueError("author does not exist")
    post = Post(
        id=_next_post_id,
        authorId=payload.authorId,
        title=payload.title,
        content=payload.content,
        createdAt=_utcnow(),
        updatedAt=_utcnow(),
    )
    _post_id_to_post[post.id] = post
    _next_post_id += 1
    return post


async def list_posts(author_id: Optional[int] = None) -> List[Post]:
    posts = list(_post_id_to_post.values())
    if author_id is not None:
        posts = [p for p in posts if p.authorId == author_id]
    return list(sorted(posts, key=lambda p: p.id))


async def get_post(post_id: int) -> Optional[Post]:
    return _post_id_to_post.get(post_id)


async def update_post(post_id: int, changes: PostUpdate) -> Optional[Post]:
    post = _post_id_to_post.get(post_id)
    if post is None:
        return None
    if changes.title is not None:
        post.title = changes.title
    if changes.content is not None:
        post.content = changes.content
    post.updatedAt = _utcnow()
    _post_id_to_post[post_id] = post
    return post


async def delete_post(post_id: int) -> bool:
    if post_id in _post_id_to_post:
        del _post_id_to_post[post_id]
        return True
    return False


async def save_data() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    users_data = [u.model_dump() for u in _user_id_to_user.values()]
    posts_data = [p.model_dump() for p in _post_id_to_post.values()]
    with USERS_FILE.open("w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2, default=str)
    with POSTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=2, default=str)


async def load_data() -> None:
    global _next_user_id, _next_post_id
    _user_id_to_user.clear()
    _post_id_to_post.clear()

    if USERS_FILE.exists():
        try:
            users_raw = json.loads(USERS_FILE.read_text(encoding="utf-8"))
            for item in users_raw:
                user = User(**item)
                _user_id_to_user[user.id] = user
        except (json.JSONDecodeError, ValidationError):
            pass
    if POSTS_FILE.exists():
        try:
            posts_raw = json.loads(POSTS_FILE.read_text(encoding="utf-8"))
            for item in posts_raw:
                post = Post(**item)
                _post_id_to_post[post.id] = post
        except (json.JSONDecodeError, ValidationError):
            pass

    _next_user_id = (max(_user_id_to_user.keys()) + 1) if _user_id_to_user else 1
    _next_post_id = (max(_post_id_to_post.keys()) + 1) if _post_id_to_post else 1
