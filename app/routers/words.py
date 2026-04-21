"""Vocabulary routes — word of the day and saved words."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.saved_word import SavedWord
from app.models.user import User
from app.schemas.words import SavedWordIn, SavedWordOut, WordOfTheDay
from app.services import words_of_day

router = APIRouter(prefix="/api/words", tags=["words"])


@router.get("/today/{user_id}", response_model=WordOfTheDay)
async def get_word_of_the_day(user_id: int, db: AsyncSession = Depends(get_session)):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return words_of_day.word_for_today(user.language)


@router.post("/saved/{user_id}", response_model=SavedWordOut)
async def save_word(
    user_id: int,
    payload: SavedWordIn,
    db: AsyncSession = Depends(get_session),
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    saved = SavedWord(
        user_id=user_id,
        word=payload.word,
        language=payload.language,
        translation=payload.translation,
        notes=payload.notes,
    )
    db.add(saved)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Word already saved")
    await db.refresh(saved)
    return saved


@router.get("/saved/{user_id}", response_model=list[SavedWordOut])
async def list_saved_words(user_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(SavedWord)
        .where(SavedWord.user_id == user_id)
        .order_by(SavedWord.created_at.desc())
    )
    return list(result.scalars().all())