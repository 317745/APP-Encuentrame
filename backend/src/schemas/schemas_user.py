from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from datetime import datetime, timezone

class AuthUser(SQLModel, table=True):
    __tablename__ = "auth_users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        nullable=False,
        index=True
    )
        
    email: str = Field(
        unique=True,
        index=True,
        max_length=255,
        nullable=False
    )

    password: str = Field(
        max_length=255,
        nullable=False
    )

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        foreign_key="auth_users.id",
        primary_key=True,
        nullable=False,
        index=True
    )

    email: str = Field(
        foreign_key="auth_users.email",
        unique=True,
        index=True,
        max_length=255,
        nullable=False
    )

    name: str = Field(
        max_length=255,
        nullable=False
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )