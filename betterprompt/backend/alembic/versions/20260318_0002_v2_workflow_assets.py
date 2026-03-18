"""v2 workflow assets schema

Revision ID: 20260318_0002
Revises: 20260318_0001
Create Date: 2026-03-18 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260318_0002'
down_revision = '20260318_0001'
branch_labels = None
depends_on = None


def _existing_tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def _existing_columns(table_name: str) -> set[str]:
    return {item['name'] for item in inspect(op.get_bind()).get_columns(table_name)}


def _existing_indexes(table_name: str) -> set[str]:
    return {item['name'] for item in inspect(op.get_bind()).get_indexes(table_name)}


def _existing_foreign_keys(table_name: str) -> set[str]:
    return {item['name'] for item in inspect(op.get_bind()).get_foreign_keys(table_name) if item.get('name')}


def upgrade() -> None:
    tables = _existing_tables()

    if 'context_packs' not in tables:
        op.create_table(
            'context_packs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('current_version_id', sa.String(length=36), nullable=True),
            sa.Column('tags_json', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('context_packs')

    if 'context_pack_versions' not in tables:
        op.create_table(
            'context_pack_versions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('context_pack_id', sa.String(length=36), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False),
            sa.Column('payload_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('source_iteration_id', sa.String(length=36), nullable=True),
            sa.Column('change_summary', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['context_pack_id'], ['context_packs.id']),
            sa.ForeignKeyConstraint(['source_iteration_id'], ['prompt_iterations.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('context_pack_versions')

    if 'evaluation_profiles' not in tables:
        op.create_table(
            'evaluation_profiles',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('current_version_id', sa.String(length=36), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('evaluation_profiles')

    if 'evaluation_profile_versions' not in tables:
        op.create_table(
            'evaluation_profile_versions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('evaluation_profile_id', sa.String(length=36), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False),
            sa.Column('rules_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('change_summary', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['evaluation_profile_id'], ['evaluation_profiles.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('evaluation_profile_versions')

    if 'workflow_recipes' not in tables:
        op.create_table(
            'workflow_recipes',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('domain_hint', sa.String(length=80), nullable=True),
            sa.Column('current_version_id', sa.String(length=36), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('workflow_recipes')

    if 'workflow_recipe_versions' not in tables:
        op.create_table(
            'workflow_recipe_versions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('workflow_recipe_id', sa.String(length=36), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False),
            sa.Column('definition_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('source_iteration_id', sa.String(length=36), nullable=True),
            sa.Column('change_summary', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['workflow_recipe_id'], ['workflow_recipes.id']),
            sa.ForeignKeyConstraint(['source_iteration_id'], ['prompt_iterations.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('workflow_recipe_versions')

    if 'run_presets' not in tables:
        op.create_table(
            'run_presets',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('definition_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('last_used_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('run_presets')

    context_pack_indexes = _existing_indexes('context_packs')
    if 'ix_context_packs_user_id' not in context_pack_indexes:
        op.create_index('ix_context_packs_user_id', 'context_packs', ['user_id'], unique=False)
    if 'idx_context_packs_user_updated_at' not in context_pack_indexes:
        op.create_index('idx_context_packs_user_updated_at', 'context_packs', ['user_id', 'updated_at'], unique=False)
    if 'idx_context_packs_user_name' not in context_pack_indexes:
        op.create_index('idx_context_packs_user_name', 'context_packs', ['user_id', 'name'], unique=False)

    context_pack_version_indexes = _existing_indexes('context_pack_versions')
    if 'ix_context_pack_versions_context_pack_id' not in context_pack_version_indexes:
        op.create_index(
            'ix_context_pack_versions_context_pack_id',
            'context_pack_versions',
            ['context_pack_id'],
            unique=False,
        )
    if 'ix_context_pack_versions_source_iteration_id' not in context_pack_version_indexes:
        op.create_index(
            'ix_context_pack_versions_source_iteration_id',
            'context_pack_versions',
            ['source_iteration_id'],
            unique=False,
        )
    if 'uq_context_pack_versions_context_pack_id_version_number' not in context_pack_version_indexes:
        op.create_index(
            'uq_context_pack_versions_context_pack_id_version_number',
            'context_pack_versions',
            ['context_pack_id', 'version_number'],
            unique=True,
        )
    if 'idx_context_pack_versions_context_pack_created_at' not in context_pack_version_indexes:
        op.create_index(
            'idx_context_pack_versions_context_pack_created_at',
            'context_pack_versions',
            ['context_pack_id', 'created_at'],
            unique=False,
        )

    evaluation_profile_indexes = _existing_indexes('evaluation_profiles')
    if 'ix_evaluation_profiles_user_id' not in evaluation_profile_indexes:
        op.create_index('ix_evaluation_profiles_user_id', 'evaluation_profiles', ['user_id'], unique=False)
    if 'idx_evaluation_profiles_user_updated_at' not in evaluation_profile_indexes:
        op.create_index(
            'idx_evaluation_profiles_user_updated_at',
            'evaluation_profiles',
            ['user_id', 'updated_at'],
            unique=False,
        )
    if 'idx_evaluation_profiles_user_name' not in evaluation_profile_indexes:
        op.create_index('idx_evaluation_profiles_user_name', 'evaluation_profiles', ['user_id', 'name'], unique=False)

    evaluation_profile_version_indexes = _existing_indexes('evaluation_profile_versions')
    if 'ix_evaluation_profile_versions_evaluation_profile_id' not in evaluation_profile_version_indexes:
        op.create_index(
            'ix_evaluation_profile_versions_evaluation_profile_id',
            'evaluation_profile_versions',
            ['evaluation_profile_id'],
            unique=False,
        )
    if 'uq_evaluation_profile_versions_profile_id_version_number' not in evaluation_profile_version_indexes:
        op.create_index(
            'uq_evaluation_profile_versions_profile_id_version_number',
            'evaluation_profile_versions',
            ['evaluation_profile_id', 'version_number'],
            unique=True,
        )
    if 'idx_evaluation_profile_versions_profile_created_at' not in evaluation_profile_version_indexes:
        op.create_index(
            'idx_evaluation_profile_versions_profile_created_at',
            'evaluation_profile_versions',
            ['evaluation_profile_id', 'created_at'],
            unique=False,
        )

    workflow_recipe_indexes = _existing_indexes('workflow_recipes')
    if 'ix_workflow_recipes_user_id' not in workflow_recipe_indexes:
        op.create_index('ix_workflow_recipes_user_id', 'workflow_recipes', ['user_id'], unique=False)
    if 'idx_workflow_recipes_user_domain_updated_at' not in workflow_recipe_indexes:
        op.create_index(
            'idx_workflow_recipes_user_domain_updated_at',
            'workflow_recipes',
            ['user_id', 'domain_hint', 'updated_at'],
            unique=False,
        )

    workflow_recipe_version_indexes = _existing_indexes('workflow_recipe_versions')
    if 'ix_workflow_recipe_versions_workflow_recipe_id' not in workflow_recipe_version_indexes:
        op.create_index(
            'ix_workflow_recipe_versions_workflow_recipe_id',
            'workflow_recipe_versions',
            ['workflow_recipe_id'],
            unique=False,
        )
    if 'ix_workflow_recipe_versions_source_iteration_id' not in workflow_recipe_version_indexes:
        op.create_index(
            'ix_workflow_recipe_versions_source_iteration_id',
            'workflow_recipe_versions',
            ['source_iteration_id'],
            unique=False,
        )
    if 'uq_workflow_recipe_versions_recipe_id_version_number' not in workflow_recipe_version_indexes:
        op.create_index(
            'uq_workflow_recipe_versions_recipe_id_version_number',
            'workflow_recipe_versions',
            ['workflow_recipe_id', 'version_number'],
            unique=True,
        )
    if 'idx_workflow_recipe_versions_recipe_created_at' not in workflow_recipe_version_indexes:
        op.create_index(
            'idx_workflow_recipe_versions_recipe_created_at',
            'workflow_recipe_versions',
            ['workflow_recipe_id', 'created_at'],
            unique=False,
        )

    run_preset_indexes = _existing_indexes('run_presets')
    if 'ix_run_presets_user_id' not in run_preset_indexes:
        op.create_index('ix_run_presets_user_id', 'run_presets', ['user_id'], unique=False)
    if 'idx_run_presets_user_last_used_at' not in run_preset_indexes:
        op.create_index(
            'idx_run_presets_user_last_used_at',
            'run_presets',
            ['user_id', 'last_used_at'],
            unique=False,
        )
    if 'idx_run_presets_user_name' not in run_preset_indexes:
        op.create_index('idx_run_presets_user_name', 'run_presets', ['user_id', 'name'], unique=False)

    if 'prompt_sessions' in tables:
        session_columns = _existing_columns('prompt_sessions')
        session_foreign_keys = _existing_foreign_keys('prompt_sessions')
        with op.batch_alter_table('prompt_sessions') as batch_op:
            if 'run_kind' not in session_columns:
                batch_op.add_column(sa.Column('run_kind', sa.String(length=32), nullable=True))
            if 'run_preset_id' not in session_columns:
                batch_op.add_column(sa.Column('run_preset_id', sa.String(length=36), nullable=True))
            if 'workflow_recipe_version_id' not in session_columns:
                batch_op.add_column(sa.Column('workflow_recipe_version_id', sa.String(length=36), nullable=True))
            if 'fk_prompt_sessions_run_preset_id' not in session_foreign_keys:
                batch_op.create_foreign_key(
                    'fk_prompt_sessions_run_preset_id',
                    'run_presets',
                    ['run_preset_id'],
                    ['id'],
                )
            if 'fk_prompt_sessions_workflow_recipe_version_id' not in session_foreign_keys:
                batch_op.create_foreign_key(
                    'fk_prompt_sessions_workflow_recipe_version_id',
                    'workflow_recipe_versions',
                    ['workflow_recipe_version_id'],
                    ['id'],
                )

        session_indexes = _existing_indexes('prompt_sessions')
        if 'ix_prompt_sessions_run_kind' not in session_indexes:
            op.create_index('ix_prompt_sessions_run_kind', 'prompt_sessions', ['run_kind'], unique=False)
        if 'ix_prompt_sessions_run_preset_id' not in session_indexes:
            op.create_index('ix_prompt_sessions_run_preset_id', 'prompt_sessions', ['run_preset_id'], unique=False)
        if 'ix_prompt_sessions_workflow_recipe_version_id' not in session_indexes:
            op.create_index(
                'ix_prompt_sessions_workflow_recipe_version_id',
                'prompt_sessions',
                ['workflow_recipe_version_id'],
                unique=False,
            )


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())

    if 'prompt_sessions' in tables:
        op.drop_index('ix_prompt_sessions_workflow_recipe_version_id', table_name='prompt_sessions', if_exists=True)
        op.drop_index('ix_prompt_sessions_run_preset_id', table_name='prompt_sessions', if_exists=True)
        op.drop_index('ix_prompt_sessions_run_kind', table_name='prompt_sessions', if_exists=True)

        session_columns = _existing_columns('prompt_sessions')
        session_foreign_keys = _existing_foreign_keys('prompt_sessions')
        with op.batch_alter_table('prompt_sessions') as batch_op:
            if 'fk_prompt_sessions_workflow_recipe_version_id' in session_foreign_keys:
                batch_op.drop_constraint('fk_prompt_sessions_workflow_recipe_version_id', type_='foreignkey')
            if 'fk_prompt_sessions_run_preset_id' in session_foreign_keys:
                batch_op.drop_constraint('fk_prompt_sessions_run_preset_id', type_='foreignkey')
            if 'workflow_recipe_version_id' in session_columns:
                batch_op.drop_column('workflow_recipe_version_id')
            if 'run_preset_id' in session_columns:
                batch_op.drop_column('run_preset_id')
            if 'run_kind' in session_columns:
                batch_op.drop_column('run_kind')

    if 'run_presets' in tables:
        op.drop_index('idx_run_presets_user_name', table_name='run_presets', if_exists=True)
        op.drop_index('idx_run_presets_user_last_used_at', table_name='run_presets', if_exists=True)
        op.drop_index('ix_run_presets_user_id', table_name='run_presets', if_exists=True)
        op.drop_table('run_presets')

    if 'workflow_recipe_versions' in tables:
        op.drop_index('idx_workflow_recipe_versions_recipe_created_at', table_name='workflow_recipe_versions', if_exists=True)
        op.drop_index(
            'uq_workflow_recipe_versions_recipe_id_version_number',
            table_name='workflow_recipe_versions',
            if_exists=True,
        )
        op.drop_index('ix_workflow_recipe_versions_source_iteration_id', table_name='workflow_recipe_versions', if_exists=True)
        op.drop_index('ix_workflow_recipe_versions_workflow_recipe_id', table_name='workflow_recipe_versions', if_exists=True)
        op.drop_table('workflow_recipe_versions')

    if 'workflow_recipes' in tables:
        op.drop_index('idx_workflow_recipes_user_domain_updated_at', table_name='workflow_recipes', if_exists=True)
        op.drop_index('ix_workflow_recipes_user_id', table_name='workflow_recipes', if_exists=True)
        op.drop_table('workflow_recipes')

    if 'evaluation_profile_versions' in tables:
        op.drop_index(
            'idx_evaluation_profile_versions_profile_created_at',
            table_name='evaluation_profile_versions',
            if_exists=True,
        )
        op.drop_index(
            'uq_evaluation_profile_versions_profile_id_version_number',
            table_name='evaluation_profile_versions',
            if_exists=True,
        )
        op.drop_index(
            'ix_evaluation_profile_versions_evaluation_profile_id',
            table_name='evaluation_profile_versions',
            if_exists=True,
        )
        op.drop_table('evaluation_profile_versions')

    if 'evaluation_profiles' in tables:
        op.drop_index('idx_evaluation_profiles_user_name', table_name='evaluation_profiles', if_exists=True)
        op.drop_index('idx_evaluation_profiles_user_updated_at', table_name='evaluation_profiles', if_exists=True)
        op.drop_index('ix_evaluation_profiles_user_id', table_name='evaluation_profiles', if_exists=True)
        op.drop_table('evaluation_profiles')

    if 'context_pack_versions' in tables:
        op.drop_index('idx_context_pack_versions_context_pack_created_at', table_name='context_pack_versions', if_exists=True)
        op.drop_index(
            'uq_context_pack_versions_context_pack_id_version_number',
            table_name='context_pack_versions',
            if_exists=True,
        )
        op.drop_index('ix_context_pack_versions_source_iteration_id', table_name='context_pack_versions', if_exists=True)
        op.drop_index('ix_context_pack_versions_context_pack_id', table_name='context_pack_versions', if_exists=True)
        op.drop_table('context_pack_versions')

    if 'context_packs' in tables:
        op.drop_index('idx_context_packs_user_name', table_name='context_packs', if_exists=True)
        op.drop_index('idx_context_packs_user_updated_at', table_name='context_packs', if_exists=True)
        op.drop_index('ix_context_packs_user_id', table_name='context_packs', if_exists=True)
        op.drop_table('context_packs')
