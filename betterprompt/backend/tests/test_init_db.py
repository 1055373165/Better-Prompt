from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from app.db import init_db as init_db_module


class InitDbTests(unittest.IsolatedAsyncioTestCase):
    async def test_init_db_runs_alembic_upgrade_when_sqlite_file_is_missing_tables(self) -> None:
        database_url = 'sqlite+aiosqlite:////tmp/betterprompt-init-db-test.db'
        fake_settings = SimpleNamespace(db_auto_create=False, database_url=database_url)
        inspect_tables = AsyncMock(side_effect=[set(), set(init_db_module.REQUIRED_TABLES)])
        run_upgrade = Mock()

        with (
            patch.object(init_db_module, 'settings', fake_settings),
            patch.object(init_db_module, '_inspect_tables', inspect_tables),
            patch.object(init_db_module, '_run_alembic_upgrade_head', run_upgrade),
        ):
            await init_db_module.init_db()

        run_upgrade.assert_called_once_with(database_url)
        self.assertEqual(inspect_tables.await_count, 2)

    async def test_init_db_raises_when_tables_are_still_missing_after_upgrade(self) -> None:
        database_url = 'sqlite+aiosqlite:////tmp/betterprompt-init-db-test.db'
        fake_settings = SimpleNamespace(db_auto_create=False, database_url=database_url)
        inspect_tables = AsyncMock(side_effect=[set(), set()])

        with (
            patch.object(init_db_module, 'settings', fake_settings),
            patch.object(init_db_module, '_inspect_tables', inspect_tables),
            patch.object(init_db_module, '_run_alembic_upgrade_head', Mock()),
        ):
            with self.assertRaises(RuntimeError) as context:
                await init_db_module.init_db()

        self.assertIn('Database schema is out of date', str(context.exception))
        self.assertIn('prompt_sessions', str(context.exception))
