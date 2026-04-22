"""Message model — every chat message stored with translation and breakdown."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    original_text: Mapped[str] = mapped_column(Text)
    original_language: Mapped[str] = mapped_column(String(5))

    translated_text: Mapped[str] = mapped_column(Text)
    translated_language: Mapped[str] = mapped_column(String(5))

    breakdown: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    # NULL until the recipient has actually opened the chat after this was sent
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None,
    )