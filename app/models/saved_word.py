"""Saved words — a personal vocabulary list each user builds."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SavedWord(Base):
    __tablename__ = "saved_words"
    __table_args__ = (UniqueConstraint("user_id", "word", "language"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    word: Mapped[str] = mapped_column(String(100))
    language: Mapped[str] = mapped_column(String(5))
    translation: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )