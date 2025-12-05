from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    login: str = Field(min_length=3, max_length=64)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    login: str | None = Field(default=None, min_length=3, max_length=64)
    password: str | None = Field(default=None, min_length=6, max_length=128)


class User(UserBase):
    id: int
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class PostBase(BaseModel):
    author_id: int = Field(alias="authorId")
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)


class Post(PostBase):
    id: int
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
