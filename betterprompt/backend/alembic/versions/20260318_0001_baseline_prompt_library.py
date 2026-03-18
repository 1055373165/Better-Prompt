"""baseline prompt library schema

Revision ID: 20260318_0001
Revises:
Create Date: 2026-03-18 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260318_0001'
down_revision = None
branch_labels = None
depends_on = None


def _existing_tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def _existing_indexes(table_name: str) -> set[str]:
    return {item['name'] for item in inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    tables = _existing_tables()

    if 'users' not in tables:
        op.create_table(
            'users',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('users')

    if 'prompt_sessions' not in tables:
        op.create_table(
            'prompt_sessions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('entry_mode', sa.String(length=32), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('latest_iteration_id', sa.String(length=36), nullable=True),
            sa.Column('metadata_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('prompt_sessions')

    if 'prompt_iterations' not in tables:
        op.create_table(
            'prompt_iterations',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('session_id', sa.String(length=36), nullable=False),
            sa.Column('parent_iteration_id', sa.String(length=36), nullable=True),
            sa.Column('mode', sa.String(length=32), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('input_payload_json', sa.Text(), nullable=False),
            sa.Column('output_payload_json', sa.Text(), nullable=False),
            sa.Column('provider', sa.String(length=64), nullable=True),
            sa.Column('model', sa.String(length=128), nullable=True),
            sa.Column('tokens_input', sa.Integer(), nullable=True),
            sa.Column('tokens_output', sa.Integer(), nullable=True),
            sa.Column('latency_ms', sa.Integer(), nullable=True),
            sa.Column('error_code', sa.String(length=64), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['session_id'], ['prompt_sessions.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('prompt_iterations')

    if 'prompt_categories' not in tables:
        op.create_table(
            'prompt_categories',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('parent_id', sa.String(length=36), nullable=True),
            sa.Column('name', sa.String(length=120), nullable=False),
            sa.Column('path', sa.String(length=1024), nullable=False),
            sa.Column('depth', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['parent_id'], ['prompt_categories.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('prompt_categories')

    if 'prompt_assets' not in tables:
        op.create_table(
            'prompt_assets',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('category_id', sa.String(length=36), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('current_version_id', sa.String(length=36), nullable=True),
            sa.Column('tags_json', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['category_id'], ['prompt_categories.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('prompt_assets')

    if 'prompt_asset_versions' not in tables:
        op.create_table(
            'prompt_asset_versions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('asset_id', sa.String(length=36), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('source_iteration_id', sa.String(length=36), nullable=True),
            sa.Column('source_asset_version_id', sa.String(length=36), nullable=True),
            sa.Column('change_summary', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['asset_id'], ['prompt_assets.id']),
            sa.ForeignKeyConstraint(['source_asset_version_id'], ['prompt_asset_versions.id']),
            sa.ForeignKeyConstraint(['source_iteration_id'], ['prompt_iterations.id']),
            sa.PrimaryKeyConstraint('id'),
        )

    user_indexes = _existing_indexes('users')
    if 'ix_users_email' not in user_indexes:
        op.create_index('ix_users_email', 'users', ['email'], unique=True)

    session_indexes = _existing_indexes('prompt_sessions')
    if 'ix_prompt_sessions_user_id' not in session_indexes:
        op.create_index('ix_prompt_sessions_user_id', 'prompt_sessions', ['user_id'], unique=False)

    iteration_indexes = _existing_indexes('prompt_iterations')
    if 'ix_prompt_iterations_session_id' not in iteration_indexes:
        op.create_index('ix_prompt_iterations_session_id', 'prompt_iterations', ['session_id'], unique=False)
    if 'ix_prompt_iterations_parent_iteration_id' not in iteration_indexes:
        op.create_index(
            'ix_prompt_iterations_parent_iteration_id',
            'prompt_iterations',
            ['parent_iteration_id'],
            unique=False,
        )

    category_indexes = _existing_indexes('prompt_categories')
    if 'ix_prompt_categories_user_id' not in category_indexes:
        op.create_index('ix_prompt_categories_user_id', 'prompt_categories', ['user_id'], unique=False)
    if 'ix_prompt_categories_parent_id' not in category_indexes:
        op.create_index('ix_prompt_categories_parent_id', 'prompt_categories', ['parent_id'], unique=False)
    if 'idx_prompt_categories_user_parent_sort' not in category_indexes:
        op.create_index(
            'idx_prompt_categories_user_parent_sort',
            'prompt_categories',
            ['user_id', 'parent_id', 'sort_order'],
            unique=False,
        )
    if 'idx_prompt_categories_user_path' not in category_indexes:
        op.create_index('idx_prompt_categories_user_path', 'prompt_categories', ['user_id', 'path'], unique=False)

    asset_indexes = _existing_indexes('prompt_assets')
    if 'ix_prompt_assets_user_id' not in asset_indexes:
        op.create_index('ix_prompt_assets_user_id', 'prompt_assets', ['user_id'], unique=False)
    if 'ix_prompt_assets_category_id' not in asset_indexes:
        op.create_index('ix_prompt_assets_category_id', 'prompt_assets', ['category_id'], unique=False)
    if 'idx_prompt_assets_user_category_updated_at' not in asset_indexes:
        op.create_index(
            'idx_prompt_assets_user_category_updated_at',
            'prompt_assets',
            ['user_id', 'category_id', 'updated_at'],
            unique=False,
        )
    if 'idx_prompt_assets_user_favorite_updated_at' not in asset_indexes:
        op.create_index(
            'idx_prompt_assets_user_favorite_updated_at',
            'prompt_assets',
            ['user_id', 'is_favorite', 'updated_at'],
            unique=False,
        )
    if 'idx_prompt_assets_user_name' not in asset_indexes:
        op.create_index('idx_prompt_assets_user_name', 'prompt_assets', ['user_id', 'name'], unique=False)

    version_indexes = _existing_indexes('prompt_asset_versions')
    if 'ix_prompt_asset_versions_asset_id' not in version_indexes:
        op.create_index('ix_prompt_asset_versions_asset_id', 'prompt_asset_versions', ['asset_id'], unique=False)
    if 'ix_prompt_asset_versions_source_iteration_id' not in version_indexes:
        op.create_index(
            'ix_prompt_asset_versions_source_iteration_id',
            'prompt_asset_versions',
            ['source_iteration_id'],
            unique=False,
        )
    if 'ix_prompt_asset_versions_source_asset_version_id' not in version_indexes:
        op.create_index(
            'ix_prompt_asset_versions_source_asset_version_id',
            'prompt_asset_versions',
            ['source_asset_version_id'],
            unique=False,
        )
    if 'uq_prompt_asset_versions_asset_id_version_number' not in version_indexes:
        op.create_index(
            'uq_prompt_asset_versions_asset_id_version_number',
            'prompt_asset_versions',
            ['asset_id', 'version_number'],
            unique=True,
        )
    if 'idx_prompt_asset_versions_asset_created_at' not in version_indexes:
        op.create_index(
            'idx_prompt_asset_versions_asset_created_at',
            'prompt_asset_versions',
            ['asset_id', 'created_at'],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())

    if 'prompt_asset_versions' in tables:
        op.drop_index('idx_prompt_asset_versions_asset_created_at', table_name='prompt_asset_versions', if_exists=True)
        op.drop_index('uq_prompt_asset_versions_asset_id_version_number', table_name='prompt_asset_versions', if_exists=True)
        op.drop_index('ix_prompt_asset_versions_source_asset_version_id', table_name='prompt_asset_versions', if_exists=True)
        op.drop_index('ix_prompt_asset_versions_source_iteration_id', table_name='prompt_asset_versions', if_exists=True)
        op.drop_index('ix_prompt_asset_versions_asset_id', table_name='prompt_asset_versions', if_exists=True)
        op.drop_table('prompt_asset_versions')

    if 'prompt_assets' in tables:
        op.drop_index('idx_prompt_assets_user_name', table_name='prompt_assets', if_exists=True)
        op.drop_index('idx_prompt_assets_user_favorite_updated_at', table_name='prompt_assets', if_exists=True)
        op.drop_index('idx_prompt_assets_user_category_updated_at', table_name='prompt_assets', if_exists=True)
        op.drop_index('ix_prompt_assets_category_id', table_name='prompt_assets', if_exists=True)
        op.drop_index('ix_prompt_assets_user_id', table_name='prompt_assets', if_exists=True)
        op.drop_table('prompt_assets')

    if 'prompt_categories' in tables:
        op.drop_index('idx_prompt_categories_user_path', table_name='prompt_categories', if_exists=True)
        op.drop_index('idx_prompt_categories_user_parent_sort', table_name='prompt_categories', if_exists=True)
        op.drop_index('ix_prompt_categories_parent_id', table_name='prompt_categories', if_exists=True)
        op.drop_index('ix_prompt_categories_user_id', table_name='prompt_categories', if_exists=True)
        op.drop_table('prompt_categories')
