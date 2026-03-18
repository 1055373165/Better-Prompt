from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


TRUE_VALUES = {'1', 'true', 'yes', 'on'}
DEFAULT_DATABASE_URL = 'sqlite+aiosqlite:///./betterprompt.db'


def _read_bool_env(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in TRUE_VALUES


@dataclass(frozen=True)
class Settings:
    database_url: str
    db_echo: bool
    db_auto_create: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv('BETTERPROMPT_DATABASE_URL', DEFAULT_DATABASE_URL).strip(),
        db_echo=_read_bool_env('BETTERPROMPT_DB_ECHO', default=False),
        db_auto_create=_read_bool_env('BETTERPROMPT_DB_AUTO_CREATE', default=False),
    )
