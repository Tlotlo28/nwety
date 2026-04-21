"""Database models — make sure every model is imported here so SQLAlchemy sees them."""
from app.models.user import User
from app.models.message import Message
from app.models.saved_word import SavedWord

__all__ = ["User", "Message", "SavedWord"]