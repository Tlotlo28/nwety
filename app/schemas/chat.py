"""Request/response shapes for chat endpoints."""
from datetime import datetime
from pydantic import BaseModel, Field


class MessageIn(BaseModel):
    """What the client sends when posting a new message."""
    text: str = Field(min_length=1, max_length=2000)
    sender_id: int


class TokenOut(BaseModel):
    """One word in the breakdown."""
    word: str
    lemma: str
    pos: str
    translation: str
    is_punct: bool


class MessageOut(BaseModel):
    """What the client receives for each message."""
    id: int
    sender_id: int
    original_text: str
    original_language: str
    translated_text: str
    translated_language: str
    breakdown: list[TokenOut]
    breakdown_translation: list[TokenOut] = []
    created_at: datetime

    class Config:
        from_attributes = True  # Allows reading from SQLAlchemy objects