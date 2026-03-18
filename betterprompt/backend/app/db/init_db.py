from sqlalchemy import text

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models import PromptAsset, PromptAssetVersion, PromptCategory, PromptIteration, PromptSession, User

settings = get_settings()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text('SELECT 1'))
        if settings.db_auto_create:
            await conn.run_sync(Base.metadata.create_all)
