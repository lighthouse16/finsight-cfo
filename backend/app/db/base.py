from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.db.metadata import db_metadata

class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models.
    """
    metadata = db_metadata

class TimestampMixin:
    """
    Mixin to automatically add created_at and updated_at fields.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

class SoftDeleteMixin:
    """
    Mixin to support soft deletes.
    """
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True
    )
