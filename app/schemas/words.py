"""Request/response shapes for vocabulary features."""
from datetime import datetime
from pydantic import BaseModel, Field


class SavedWordIn(BaseModel):
    word: str = Field(min_length=1, max_length=100)
    language: str = Field(pattern="^(en|pt)$")
    translation: str = Field(min_length=1, max_length=200)
    notes: str | None = None


class SavedWordOut(BaseModel):
    id: int
    user_id: int
    word: str
    language: str
    translation: str
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class WordOfTheDay(BaseModel):
    word: str
    language: str
    translation: str
    pronunciation_hint: str | None = None
    example_sentence: str | None = None
    example_translation: str | None = None
    theme: str | None = None