from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models import AgentAlert
from app.models import AgentMonitor
from app.models import AgentRun
from app.models import (
    ContextPack,
    ContextPackVersion,
    DomainWorkspace,
    EvaluationProfile,
    EvaluationProfileVersion,
    FreshnessRecord,
    PromptAsset,
    PromptAssetVersion,
    PromptCategory,
    PromptIteration,
    PromptSession,
    ResearchReport,
    ResearchReportVersion,
    ResearchSource,
    RunPreset,
    User,
    Watchlist,
    WatchlistItem,
    WorkflowRecipe,
    WorkflowRecipeVersion,
    WorkspaceSubject,
)

settings = get_settings()
BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = BACKEND_ROOT / 'alembic.ini'
ALEMBIC_SCRIPT_PATH = BACKEND_ROOT / 'alembic'
REQUIRED_TABLES = {
    PromptSession.__tablename__,
    PromptIteration.__tablename__,
    PromptCategory.__tablename__,
    PromptAsset.__tablename__,
    PromptAssetVersion.__tablename__,
    Watchlist.__tablename__,
    WatchlistItem.__tablename__,
    AgentMonitor.__tablename__,
    AgentRun.__tablename__,
    AgentAlert.__tablename__,
    FreshnessRecord.__tablename__,
    DomainWorkspace.__tablename__,
    WorkspaceSubject.__tablename__,
    ResearchSource.__tablename__,
    ResearchReport.__tablename__,
    ResearchReportVersion.__tablename__,
    ContextPack.__tablename__,
    ContextPackVersion.__tablename__,
    EvaluationProfile.__tablename__,
    EvaluationProfileVersion.__tablename__,
    WorkflowRecipe.__tablename__,
    WorkflowRecipeVersion.__tablename__,
    RunPreset.__tablename__,
}


def _get_table_names(sync_connection) -> set[str]:
    return set(inspect(sync_connection).get_table_names())


def _sqlite_path_from_url(database_url: str) -> Path | None:
    prefixes = ('sqlite+aiosqlite:///', 'sqlite:///')
    for prefix in prefixes:
        if database_url.startswith(prefix):
            raw_path = database_url[len(prefix):]
            return Path(raw_path).expanduser()
    return None


def _is_file_sqlite_database(database_url: str) -> bool:
    return _sqlite_path_from_url(database_url) is not None


def _run_alembic_upgrade_head(database_url: str) -> None:
    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option('script_location', str(ALEMBIC_SCRIPT_PATH))
    config.set_main_option('prepend_sys_path', str(BACKEND_ROOT))
    config.set_main_option('sqlalchemy.url', database_url)
    command.upgrade(config, 'head')


async def _inspect_tables() -> set[str]:
    async with engine.begin() as conn:
        await conn.execute(text('SELECT 1'))
        if settings.db_auto_create:
            await conn.run_sync(Base.metadata.create_all)
        return await conn.run_sync(_get_table_names)


async def init_db() -> None:
    existing_tables = await _inspect_tables()

    missing_tables = sorted(REQUIRED_TABLES - existing_tables)
    if missing_tables and not settings.db_auto_create and _is_file_sqlite_database(settings.database_url):
        await asyncio.to_thread(_run_alembic_upgrade_head, settings.database_url)
        existing_tables = await _inspect_tables()
        missing_tables = sorted(REQUIRED_TABLES - existing_tables)

    if missing_tables:
        joined = ', '.join(missing_tables)
        raise RuntimeError(
            'Database schema is out of date. '
            f'Missing tables: {joined}. '
            'Run `betterprompt/backend/.venv/bin/alembic -c betterprompt/backend/alembic.ini upgrade head` '
            'or start the app with `./scripts/betterprompt-dev.sh start`.'
        )
