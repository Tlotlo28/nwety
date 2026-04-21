"""Content library — TV shows and tips."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.services import content_library

router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("/library/{user_id}")
async def get_library(user_id: int, db: AsyncSession = Depends(get_session)):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return content_library.get_library_for_user(user.language)