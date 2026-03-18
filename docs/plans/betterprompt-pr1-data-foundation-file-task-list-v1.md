# BetterPrompt PR-1 Data Foundation File Task List v1

## Objective

PR-1 establishes the data foundation for `Prompt Library + Workbench` without implementing library behavior yet.

This PR should only do:

- env-driven database configuration
- Alembic migration scaffold
- baseline migration for current + new schema
- new ORM models for categories, assets, and asset versions
- base API schemas for future asset APIs

This PR should not do:

- asset routes or services
- library pages
- save-to-asset behavior
- auth, billing, templates, or team scope

## File-by-File Tasks

### Docs

- `docs/plans/betterprompt-pr1-data-foundation-file-task-list-v1.md`
  - Track the exact file-level scope for PR-1.

### Backend config and boot

- `betterprompt/backend/pyproject.toml`
  - Add database foundation dependencies needed for migrations and future Postgres support.

- `betterprompt/backend/.env.example`
  - Add documented DB environment variables with safe defaults and production guidance.

- `betterprompt/backend/app/core/config.py`
  - Introduce central runtime settings for DB URL, SQL echo, and optional local auto-create.

- `betterprompt/backend/app/core/__init__.py`
  - Re-export settings helpers.

- `betterprompt/backend/app/main.py`
  - Ensure env loading happens before any module that constructs the DB engine.

- `betterprompt/backend/app/db/session.py`
  - Replace hardcoded SQLite URL with env-driven config.
  - Expose a helper Alembic can reuse.

- `betterprompt/backend/app/db/init_db.py`
  - Stop unconditional schema creation.
  - Only allow `create_all` when explicitly enabled for local bootstrap.

### ORM models

- `betterprompt/backend/app/models/prompt_category.py`
  - Add nested category model.

- `betterprompt/backend/app/models/prompt_asset.py`
  - Add prompt asset model.

- `betterprompt/backend/app/models/prompt_asset_version.py`
  - Add prompt asset version model.

- `betterprompt/backend/app/models/__init__.py`
  - Register new models so metadata and Alembic can see them.

### Future API contract foundation

- `betterprompt/backend/app/schemas/prompt_asset.py`
  - Define request/response schemas for categories, assets, and versions.

### Alembic

- `betterprompt/backend/alembic.ini`
  - Add standard Alembic config entrypoint.

- `betterprompt/backend/alembic/env.py`
  - Load runtime env, import metadata, and run async migrations.

- `betterprompt/backend/alembic/script.py.mako`
  - Add standard revision template.

- `betterprompt/backend/alembic/versions/20260318_0001_baseline_prompt_library.py`
  - Create baseline/adoption migration for current schema plus prompt library tables.

## Acceptance Checklist

- app boots with env-driven DB settings
- local SQLite still works by default
- Alembic scaffold exists and points at application metadata
- baseline migration contains current schema plus prompt library tables
- new models are importable and registered in metadata
- no route/service behavior for library features is added yet
