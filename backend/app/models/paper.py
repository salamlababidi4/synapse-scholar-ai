from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.base import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    authors: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    abstract: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    doi: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    publication_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    pdf_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )