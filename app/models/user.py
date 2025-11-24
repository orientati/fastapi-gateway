from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import String, DateTime, Integer, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, index=False, default=False)
    hashed_password: Mapped[str] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user",  # noqa: F821
                                                     cascade="all, delete-orphan")
