from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Column,
    ForeignKey,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base

# Association table for Post <-> Tag (Many-to-Many)
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    login: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author", cascade="all, delete")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user", cascade="all, delete")

    # Subscriptions: User follows others
    # We need an association table or self-referential relationship.
    # To match the schema: 'subscriptions' table with follower_id, followee_id
    following: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        foreign_keys="[Subscription.follower_id]",
        back_populates="follower",
        cascade="all, delete",
    )
    followers: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        foreign_keys="[Subscription.followee_id]",
        back_populates="followee",
        cascade="all, delete",
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    author: Mapped["User"] = relationship(back_populates="posts")
    tags: Mapped[list["Tag"]] = relationship(secondary=post_tags, back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post", cascade="all, delete")
    favorited_by: Mapped[list["Favorite"]] = relationship(back_populates="post", cascade="all, delete")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)

    posts: Mapped[list["Post"]] = relationship(secondary=post_tags, back_populates="tags")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    post: Mapped["Post"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments")


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="favorites")
    post: Mapped["Post"] = relationship(back_populates="favorited_by")


class Subscription(Base):
    __tablename__ = "subscriptions"

    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    followee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    follower: Mapped["User"] = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followee: Mapped["User"] = relationship("User", foreign_keys=[followee_id], back_populates="followers")

    __table_args__ = (CheckConstraint("follower_id != followee_id", name="check_not_self_follow"),)
