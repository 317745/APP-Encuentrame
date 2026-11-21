from sqlmodel import SQLModel, Field, UniqueConstraint
from typing import Optional
import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column

class Cats(SQLModel, table=True):
    __tablename__ = "cats"

    __table_args__ = (
        UniqueConstraint("actor_id", "name", name="idx_actor_cat_name"),
    )

    id: uuid.UUID = Field(
        default_factory = uuid.uuid4,
        primary_key = True,
        nullable = False,
        index = True
    )
    
    name: str = Field(
        max_length = 100,
        nullable = False
    )

    actor_id: uuid.UUID = Field(
        nullable=False,
        index=True
    )

    actor_type: str = Field(
        max_length=50,
        nullable=False
    )

    status: bool = Field(
        default=True,
        nullable = False
    )
    
    comuna: str = Field(
        max_length = 255,
        nullable = False
    )

    created_at: datetime = Field(
        default_factory = lambda: datetime.now(timezone.utc),
        nullable = False
    )

class CatPhotos(SQLModel, table=True):
    __tablename__ = "photos_cats"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        nullable=False,
        index=True
    )

    cat_id: uuid.UUID = Field(
        foreign_key="cats.id",
        nullable=False,
        index=True
    )

    image_url: str = Field(
        unique=True,
        nullable=False
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class CatEmbeddings(SQLModel, table=True):
    __tablename__ = "embeddings_cats"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        nullable=False,
        index=True
    )

    cat_id: uuid.UUID = Field(
        foreign_key="cats.id",
        nullable=False,
        index=True
    )

    photo_id: uuid.UUID = Field(
        foreign_key="photos_cats.id", 
        nullable=False, unique=True, 
        index=True
    )

    embedding: list[float] = Field(
        sa_column=Column(Vector(512), nullable=False)
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )