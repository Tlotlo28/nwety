"""Chat routes — send, list, and lazy breakdown."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import MessageIn, MessageOut
from app.services import translator

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/messages", response_model=MessageOut)
async def send_message(payload: MessageIn, db: AsyncSession = Depends(get_session)):
    """Translate and save — breakdown is computed lazily when requested."""
    sender = await db.get(User, payload.sender_id)
    if sender is None:
        raise HTTPException(status_code=404, detail="Sender not found")

    to_language = "pt" if sender.language == "en" else "en"
    translated = translator.translate(payload.text, sender.language, to_language)

    message = Message(
        sender_id=sender.id,
        original_text=payload.text,
        original_language=sender.language,
        translated_text=translated,
        translated_language=to_language,
        breakdown=[],
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    return MessageOut(
        id=message.id, sender_id=message.sender_id,
        original_text=message.original_text, original_language=message.original_language,
        translated_text=message.translated_text, translated_language=message.translated_language,
        breakdown=[], breakdown_translation=[], created_at=message.created_at,
    )


@router.get("/messages", response_model=list[MessageOut])
async def list_messages(limit: int = 50, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Message).order_by(Message.created_at.desc()).limit(limit)
    )
    messages = list(result.scalars().all())
    messages.reverse()
    return [
        MessageOut(
            id=m.id, sender_id=m.sender_id,
            original_text=m.original_text, original_language=m.original_language,
            translated_text=m.translated_text, translated_language=m.translated_language,
            breakdown=[], breakdown_translation=[], created_at=m.created_at,
        )
        for m in messages
    ]


@router.get("/messages/{message_id}/breakdown")
async def get_breakdown(
    message_id: int,
    which: str = Query("translation", pattern="^(original|translation)$"),
    db: AsyncSession = Depends(get_session),
):
    """Break down a message's original or translated text into learning tokens."""
    message = await db.get(Message, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    if which == "original":
        text, lang = message.original_text, message.original_language
    else:
        text, lang = message.translated_text, message.translated_language
    return {"tokens": translator.break_down(text, lang)}