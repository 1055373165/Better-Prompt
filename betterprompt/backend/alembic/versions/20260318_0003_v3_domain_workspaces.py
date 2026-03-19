"""v3 domain workspaces schema

Revision ID: 20260318_0003
Revises: 20260318_0002
Create Date: 2026-03-18 15:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260318_0003'
down_revision = '20260318_0002'
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

    if 'domain_workspaces' not in tables:
        op.create_table(
            'domain_workspaces',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('workspace_type', sa.String(length=80), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=40), nullable=False, server_default='active'),
            sa.Column('config_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('domain_workspaces')

    if 'workspace_subjects' not in tables:
        op.create_table(
            'workspace_subjects',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('workspace_id', sa.String(length=36), nullable=False),
            sa.Column('subject_type', sa.String(length=80), nullable=False),
            sa.Column('external_key', sa.String(length=255), nullable=True),
            sa.Column('display_name', sa.String(length=255), nullable=False),
            sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('status', sa.String(length=40), nullable=False, server_default='active'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['workspace_id'], ['domain_workspaces.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('workspace_subjects')

    if 'research_sources' not in tables:
        op.create_table(
            'research_sources',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('workspace_id', sa.String(length=36), nullable=False),
            sa.Column('subject_id', sa.String(length=36), nullable=True),
            sa.Column('source_type', sa.String(length=40), nullable=False),
            sa.Column('canonical_uri', sa.String(length=2048), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=True),
            sa.Column('content_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('source_timestamp', sa.DateTime(), nullable=True),
            sa.Column('ingest_status', sa.String(length=40), nullable=False, server_default='ready'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['workspace_id'], ['domain_workspaces.id']),
            sa.ForeignKeyConstraint(['subject_id'], ['workspace_subjects.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('research_sources')

    if 'research_reports' not in tables:
        op.create_table(
            'research_reports',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('workspace_id', sa.String(length=36), nullable=False),
            sa.Column('subject_id', sa.String(length=36), nullable=True),
            sa.Column('report_type', sa.String(length=80), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('latest_version_id', sa.String(length=36), nullable=True),
            sa.Column('status', sa.String(length=40), nullable=False, server_default='active'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['workspace_id'], ['domain_workspaces.id']),
            sa.ForeignKeyConstraint(['subject_id'], ['workspace_subjects.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('research_reports')

    if 'research_report_versions' not in tables:
        op.create_table(
            'research_report_versions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('report_id', sa.String(length=36), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False),
            sa.Column('content_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('summary_text', sa.Text(), nullable=True),
            sa.Column('source_session_id', sa.String(length=36), nullable=True),
            sa.Column('source_iteration_id', sa.String(length=36), nullable=True),
            sa.Column('confidence_score', sa.Numeric(precision=4, scale=2), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['report_id'], ['research_reports.id']),
            sa.ForeignKeyConstraint(['source_session_id'], ['prompt_sessions.id']),
            sa.ForeignKeyConstraint(['source_iteration_id'], ['prompt_iterations.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('research_report_versions')

    domain_workspace_indexes = _existing_indexes('domain_workspaces')
    if 'ix_domain_workspaces_user_id' not in domain_workspace_indexes:
        op.create_index('ix_domain_workspaces_user_id', 'domain_workspaces', ['user_id'], unique=False)
    if 'ix_domain_workspaces_workspace_type' not in domain_workspace_indexes:
        op.create_index('ix_domain_workspaces_workspace_type', 'domain_workspaces', ['workspace_type'], unique=False)
    if 'idx_domain_workspaces_user_workspace_type_updated_at' not in domain_workspace_indexes:
        op.create_index(
            'idx_domain_workspaces_user_workspace_type_updated_at',
            'domain_workspaces',
            ['user_id', 'workspace_type', 'updated_at'],
            unique=False,
        )
    if 'idx_domain_workspaces_user_updated_at' not in domain_workspace_indexes:
        op.create_index(
            'idx_domain_workspaces_user_updated_at',
            'domain_workspaces',
            ['user_id', 'updated_at'],
            unique=False,
        )

    workspace_subject_indexes = _existing_indexes('workspace_subjects')
    if 'ix_workspace_subjects_workspace_id' not in workspace_subject_indexes:
        op.create_index('ix_workspace_subjects_workspace_id', 'workspace_subjects', ['workspace_id'], unique=False)
    if 'ix_workspace_subjects_subject_type' not in workspace_subject_indexes:
        op.create_index('ix_workspace_subjects_subject_type', 'workspace_subjects', ['subject_type'], unique=False)
    if 'idx_workspace_subjects_workspace_updated_at' not in workspace_subject_indexes:
        op.create_index(
            'idx_workspace_subjects_workspace_updated_at',
            'workspace_subjects',
            ['workspace_id', 'updated_at'],
            unique=False,
        )
    if 'idx_workspace_subjects_workspace_subject_type_updated_at' not in workspace_subject_indexes:
        op.create_index(
            'idx_workspace_subjects_workspace_subject_type_updated_at',
            'workspace_subjects',
            ['workspace_id', 'subject_type', 'updated_at'],
            unique=False,
        )
    if 'idx_workspace_subjects_workspace_subject_type_external_key' not in workspace_subject_indexes:
        op.create_index(
            'idx_workspace_subjects_workspace_subject_type_external_key',
            'workspace_subjects',
            ['workspace_id', 'subject_type', 'external_key'],
            unique=False,
        )

    research_source_indexes = _existing_indexes('research_sources')
    if 'ix_research_sources_workspace_id' not in research_source_indexes:
        op.create_index('ix_research_sources_workspace_id', 'research_sources', ['workspace_id'], unique=False)
    if 'ix_research_sources_subject_id' not in research_source_indexes:
        op.create_index('ix_research_sources_subject_id', 'research_sources', ['subject_id'], unique=False)
    if 'ix_research_sources_source_type' not in research_source_indexes:
        op.create_index('ix_research_sources_source_type', 'research_sources', ['source_type'], unique=False)
    if 'idx_research_sources_workspace_subject_updated_at' not in research_source_indexes:
        op.create_index(
            'idx_research_sources_workspace_subject_updated_at',
            'research_sources',
            ['workspace_id', 'subject_id', 'updated_at'],
            unique=False,
        )
    if 'idx_research_sources_workspace_type_source_timestamp' not in research_source_indexes:
        op.create_index(
            'idx_research_sources_workspace_type_source_timestamp',
            'research_sources',
            ['workspace_id', 'source_type', 'source_timestamp'],
            unique=False,
        )

    research_report_indexes = _existing_indexes('research_reports')
    if 'ix_research_reports_workspace_id' not in research_report_indexes:
        op.create_index('ix_research_reports_workspace_id', 'research_reports', ['workspace_id'], unique=False)
    if 'ix_research_reports_subject_id' not in research_report_indexes:
        op.create_index('ix_research_reports_subject_id', 'research_reports', ['subject_id'], unique=False)
    if 'ix_research_reports_report_type' not in research_report_indexes:
        op.create_index('ix_research_reports_report_type', 'research_reports', ['report_type'], unique=False)
    if 'idx_research_reports_workspace_subject_updated_at' not in research_report_indexes:
        op.create_index(
            'idx_research_reports_workspace_subject_updated_at',
            'research_reports',
            ['workspace_id', 'subject_id', 'updated_at'],
            unique=False,
        )
    if 'idx_research_reports_workspace_report_type_updated_at' not in research_report_indexes:
        op.create_index(
            'idx_research_reports_workspace_report_type_updated_at',
            'research_reports',
            ['workspace_id', 'report_type', 'updated_at'],
            unique=False,
        )

    research_report_version_indexes = _existing_indexes('research_report_versions')
    if 'ix_research_report_versions_report_id' not in research_report_version_indexes:
        op.create_index(
            'ix_research_report_versions_report_id',
            'research_report_versions',
            ['report_id'],
            unique=False,
        )
    if 'ix_research_report_versions_source_session_id' not in research_report_version_indexes:
        op.create_index(
            'ix_research_report_versions_source_session_id',
            'research_report_versions',
            ['source_session_id'],
            unique=False,
        )
    if 'ix_research_report_versions_source_iteration_id' not in research_report_version_indexes:
        op.create_index(
            'ix_research_report_versions_source_iteration_id',
            'research_report_versions',
            ['source_iteration_id'],
            unique=False,
        )
    if 'uq_research_report_versions_report_id_version_number' not in research_report_version_indexes:
        op.create_index(
            'uq_research_report_versions_report_id_version_number',
            'research_report_versions',
            ['report_id', 'version_number'],
            unique=True,
        )
    if 'idx_research_report_versions_report_created_at' not in research_report_version_indexes:
        op.create_index(
            'idx_research_report_versions_report_created_at',
            'research_report_versions',
            ['report_id', 'created_at'],
            unique=False,
        )

    if 'prompt_sessions' in tables:
        session_columns = _existing_columns('prompt_sessions')
        session_foreign_keys = _existing_foreign_keys('prompt_sessions')
        with op.batch_alter_table('prompt_sessions') as batch_op:
            if 'domain_workspace_id' not in session_columns:
                batch_op.add_column(sa.Column('domain_workspace_id', sa.String(length=36), nullable=True))
            if 'subject_id' not in session_columns:
                batch_op.add_column(sa.Column('subject_id', sa.String(length=36), nullable=True))
            if 'fk_prompt_sessions_domain_workspace_id' not in session_foreign_keys:
                batch_op.create_foreign_key(
                    'fk_prompt_sessions_domain_workspace_id',
                    'domain_workspaces',
                    ['domain_workspace_id'],
                    ['id'],
                )
            if 'fk_prompt_sessions_subject_id' not in session_foreign_keys:
                batch_op.create_foreign_key(
                    'fk_prompt_sessions_subject_id',
                    'workspace_subjects',
                    ['subject_id'],
                    ['id'],
                )

        session_indexes = _existing_indexes('prompt_sessions')
        if 'ix_prompt_sessions_domain_workspace_id' not in session_indexes:
            op.create_index(
                'ix_prompt_sessions_domain_workspace_id',
                'prompt_sessions',
                ['domain_workspace_id'],
                unique=False,
            )
        if 'ix_prompt_sessions_subject_id' not in session_indexes:
            op.create_index('ix_prompt_sessions_subject_id', 'prompt_sessions', ['subject_id'], unique=False)


def downgrade() -> None:
    tables = _existing_tables()

    if 'prompt_sessions' in tables:
        op.drop_index('ix_prompt_sessions_subject_id', table_name='prompt_sessions', if_exists=True)
        op.drop_index('ix_prompt_sessions_domain_workspace_id', table_name='prompt_sessions', if_exists=True)

        session_columns = _existing_columns('prompt_sessions')
        session_foreign_keys = _existing_foreign_keys('prompt_sessions')
        with op.batch_alter_table('prompt_sessions') as batch_op:
            if 'fk_prompt_sessions_subject_id' in session_foreign_keys:
                batch_op.drop_constraint('fk_prompt_sessions_subject_id', type_='foreignkey')
            if 'fk_prompt_sessions_domain_workspace_id' in session_foreign_keys:
                batch_op.drop_constraint('fk_prompt_sessions_domain_workspace_id', type_='foreignkey')
            if 'subject_id' in session_columns:
                batch_op.drop_column('subject_id')
            if 'domain_workspace_id' in session_columns:
                batch_op.drop_column('domain_workspace_id')

    if 'research_report_versions' in tables:
        op.drop_index(
            'idx_research_report_versions_report_created_at',
            table_name='research_report_versions',
            if_exists=True,
        )
        op.drop_index(
            'uq_research_report_versions_report_id_version_number',
            table_name='research_report_versions',
            if_exists=True,
        )
        op.drop_index(
            'ix_research_report_versions_source_iteration_id',
            table_name='research_report_versions',
            if_exists=True,
        )
        op.drop_index(
            'ix_research_report_versions_source_session_id',
            table_name='research_report_versions',
            if_exists=True,
        )
        op.drop_index('ix_research_report_versions_report_id', table_name='research_report_versions', if_exists=True)
        op.drop_table('research_report_versions')

    if 'research_reports' in tables:
        op.drop_index(
            'idx_research_reports_workspace_report_type_updated_at',
            table_name='research_reports',
            if_exists=True,
        )
        op.drop_index(
            'idx_research_reports_workspace_subject_updated_at',
            table_name='research_reports',
            if_exists=True,
        )
        op.drop_index('ix_research_reports_report_type', table_name='research_reports', if_exists=True)
        op.drop_index('ix_research_reports_subject_id', table_name='research_reports', if_exists=True)
        op.drop_index('ix_research_reports_workspace_id', table_name='research_reports', if_exists=True)
        op.drop_table('research_reports')

    if 'research_sources' in tables:
        op.drop_index(
            'idx_research_sources_workspace_type_source_timestamp',
            table_name='research_sources',
            if_exists=True,
        )
        op.drop_index(
            'idx_research_sources_workspace_subject_updated_at',
            table_name='research_sources',
            if_exists=True,
        )
        op.drop_index('ix_research_sources_source_type', table_name='research_sources', if_exists=True)
        op.drop_index('ix_research_sources_subject_id', table_name='research_sources', if_exists=True)
        op.drop_index('ix_research_sources_workspace_id', table_name='research_sources', if_exists=True)
        op.drop_table('research_sources')

    if 'workspace_subjects' in tables:
        op.drop_index(
            'idx_workspace_subjects_workspace_subject_type_external_key',
            table_name='workspace_subjects',
            if_exists=True,
        )
        op.drop_index(
            'idx_workspace_subjects_workspace_subject_type_updated_at',
            table_name='workspace_subjects',
            if_exists=True,
        )
        op.drop_index('idx_workspace_subjects_workspace_updated_at', table_name='workspace_subjects', if_exists=True)
        op.drop_index('ix_workspace_subjects_subject_type', table_name='workspace_subjects', if_exists=True)
        op.drop_index('ix_workspace_subjects_workspace_id', table_name='workspace_subjects', if_exists=True)
        op.drop_table('workspace_subjects')

    if 'domain_workspaces' in tables:
        op.drop_index(
            'idx_domain_workspaces_user_updated_at',
            table_name='domain_workspaces',
            if_exists=True,
        )
        op.drop_index(
            'idx_domain_workspaces_user_workspace_type_updated_at',
            table_name='domain_workspaces',
            if_exists=True,
        )
        op.drop_index('ix_domain_workspaces_workspace_type', table_name='domain_workspaces', if_exists=True)
        op.drop_index('ix_domain_workspaces_user_id', table_name='domain_workspaces', if_exists=True)
        op.drop_table('domain_workspaces')
