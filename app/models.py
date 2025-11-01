from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    login: str | None = Field(default=None, min_length=3, max_length=64)
    password: str | None = Field(default=None, min_length=6, max_length=128)


class User(UserBase):
    id: int
    createdAt: datetime
    updatedAt: datetime


class PostBase(BaseModel):
    authorId: int
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)


class Post(PostBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
