"""v4 freshness aware agents schema

Revision ID: 20260319_0004
Revises: 20260318_0003
Create Date: 2026-03-19 02:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260319_0004'
down_revision = '20260318_0003'
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

    if 'watchlists' not in tables:
        op.create_table(
            'watchlists',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('workspace_id', sa.String(length=36), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=40), nullable=False, server_default='active'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['workspace_id'], ['domain_workspaces.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('watchlists')

    if 'watchlist_items' not in tables:
        op.create_table(
            'watchlist_items',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('watchlist_id', sa.String(length=36), nullable=False),
            sa.Column('subject_id', sa.String(length=36), nullable=False),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['watchlist_id'], ['watchlists.id']),
            sa.ForeignKeyConstraint(['subject_id'], ['workspace_subjects.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('watchlist_id', 'subject_id', name='uq_watchlist_items_watchlist_subject'),
        )
        tables.add('watchlist_items')

    if 'agent_monitors' not in tables:
        op.create_table(
            'agent_monitors',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('workspace_id', sa.String(length=36), nullable=False),
            sa.Column('watchlist_id', sa.String(length=36), nullable=True),
            sa.Column('subject_id', sa.String(length=36), nullable=True),
            sa.Column('run_preset_id', sa.String(length=36), nullable=True),
            sa.Column('workflow_recipe_version_id', sa.String(length=36), nullable=True),
            sa.Column('monitor_type', sa.String(length=40), nullable=False),
            sa.Column('status', sa.String(length=40), nullable=False, server_default='active'),
            sa.Column('trigger_config_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('alert_policy_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('last_run_at', sa.DateTime(), nullable=True),
            sa.Column('next_run_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['workspace_id'], ['domain_workspaces.id']),
            sa.ForeignKeyConstraint(['watchlist_id'], ['watchlists.id']),
            sa.ForeignKeyConstraint(['subject_id'], ['workspace_subjects.id']),
            sa.ForeignKeyConstraint(['run_preset_id'], ['run_presets.id']),
            sa.ForeignKeyConstraint(['workflow_recipe_version_id'], ['workflow_recipe_versions.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('agent_monitors')

    if 'agent_runs' not in tables:
        op.create_table(
            'agent_runs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('monitor_id', sa.String(length=36), nullable=False),
            sa.Column('workspace_id', sa.String(length=36), nullable=False),
            sa.Column('subject_id', sa.String(length=36), nullable=True),
            sa.Column('previous_run_id', sa.String(length=36), nullable=True),
            sa.Column('prompt_session_id', sa.String(length=36), nullable=True),
            sa.Column('prompt_iteration_id', sa.String(length=36), nullable=True),
            sa.Column('trigger_kind', sa.String(length=40), nullable=True),
            sa.Column('run_status', sa.String(length=40), nullable=False, server_default='completed'),
            sa.Column('input_freshness_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('change_summary_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('conclusion_summary', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('finished_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['monitor_id'], ['agent_monitors.id']),
            sa.ForeignKeyConstraint(['workspace_id'], ['domain_workspaces.id']),
            sa.ForeignKeyConstraint(['subject_id'], ['workspace_subjects.id']),
            sa.ForeignKeyConstraint(['previous_run_id'], ['agent_runs.id']),
            sa.ForeignKeyConstraint(['prompt_session_id'], ['prompt_sessions.id']),
            sa.ForeignKeyConstraint(['prompt_iteration_id'], ['prompt_iterations.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('agent_runs')

    if 'agent_alerts' not in tables:
        op.create_table(
            'agent_alerts',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('workspace_id', sa.String(length=36), nullable=False),
            sa.Column('subject_id', sa.String(length=36), nullable=True),
            sa.Column('run_id', sa.String(length=36), nullable=False),
            sa.Column('severity', sa.String(length=40), nullable=False),
            sa.Column('status', sa.String(length=40), nullable=False, server_default='unread'),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('summary_text', sa.Text(), nullable=True),
            sa.Column('payload_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['workspace_id'], ['domain_workspaces.id']),
            sa.ForeignKeyConstraint(['subject_id'], ['workspace_subjects.id']),
            sa.ForeignKeyConstraint(['run_id'], ['agent_runs.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('agent_alerts')

    if 'freshness_records' not in tables:
        op.create_table(
            'freshness_records',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('workspace_id', sa.String(length=36), nullable=False),
            sa.Column('subject_id', sa.String(length=36), nullable=True),
            sa.Column('source_id', sa.String(length=36), nullable=True),
            sa.Column('report_id', sa.String(length=36), nullable=True),
            sa.Column('status', sa.String(length=40), nullable=False),
            sa.Column('observed_at', sa.DateTime(), nullable=False),
            sa.Column('last_checked_at', sa.DateTime(), nullable=True),
            sa.Column('data_timestamp', sa.DateTime(), nullable=True),
            sa.Column('details_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['workspace_id'], ['domain_workspaces.id']),
            sa.ForeignKeyConstraint(['subject_id'], ['workspace_subjects.id']),
            sa.ForeignKeyConstraint(['source_id'], ['research_sources.id']),
            sa.ForeignKeyConstraint(['report_id'], ['research_reports.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('freshness_records')

    watchlist_indexes = _existing_indexes('watchlists')
    if 'ix_watchlists_user_id' not in watchlist_indexes:
        op.create_index('ix_watchlists_user_id', 'watchlists', ['user_id'], unique=False)
    if 'ix_watchlists_workspace_id' not in watchlist_indexes:
        op.create_index('ix_watchlists_workspace_id', 'watchlists', ['workspace_id'], unique=False)
    if 'idx_watchlists_workspace_updated_at' not in watchlist_indexes:
        op.create_index(
            'idx_watchlists_workspace_updated_at',
            'watchlists',
            ['workspace_id', 'updated_at'],
            unique=False,
        )

    watchlist_item_indexes = _existing_indexes('watchlist_items')
    if 'ix_watchlist_items_watchlist_id' not in watchlist_item_indexes:
        op.create_index('ix_watchlist_items_watchlist_id', 'watchlist_items', ['watchlist_id'], unique=False)
    if 'ix_watchlist_items_subject_id' not in watchlist_item_indexes:
        op.create_index('ix_watchlist_items_subject_id', 'watchlist_items', ['subject_id'], unique=False)
    if 'idx_watchlist_items_watchlist_sort_order' not in watchlist_item_indexes:
        op.create_index(
            'idx_watchlist_items_watchlist_sort_order',
            'watchlist_items',
            ['watchlist_id', 'sort_order'],
            unique=False,
        )

    agent_monitor_indexes = _existing_indexes('agent_monitors')
    if 'ix_agent_monitors_user_id' not in agent_monitor_indexes:
        op.create_index('ix_agent_monitors_user_id', 'agent_monitors', ['user_id'], unique=False)
    if 'ix_agent_monitors_workspace_id' not in agent_monitor_indexes:
        op.create_index('ix_agent_monitors_workspace_id', 'agent_monitors', ['workspace_id'], unique=False)
    if 'ix_agent_monitors_watchlist_id' not in agent_monitor_indexes:
        op.create_index('ix_agent_monitors_watchlist_id', 'agent_monitors', ['watchlist_id'], unique=False)
    if 'ix_agent_monitors_subject_id' not in agent_monitor_indexes:
        op.create_index('ix_agent_monitors_subject_id', 'agent_monitors', ['subject_id'], unique=False)
    if 'ix_agent_monitors_run_preset_id' not in agent_monitor_indexes:
        op.create_index('ix_agent_monitors_run_preset_id', 'agent_monitors', ['run_preset_id'], unique=False)
    if 'ix_agent_monitors_workflow_recipe_version_id' not in agent_monitor_indexes:
        op.create_index(
            'ix_agent_monitors_workflow_recipe_version_id',
            'agent_monitors',
            ['workflow_recipe_version_id'],
            unique=False,
        )
    if 'ix_agent_monitors_monitor_type' not in agent_monitor_indexes:
        op.create_index('ix_agent_monitors_monitor_type', 'agent_monitors', ['monitor_type'], unique=False)
    if 'ix_agent_monitors_status' not in agent_monitor_indexes:
        op.create_index('ix_agent_monitors_status', 'agent_monitors', ['status'], unique=False)
    if 'idx_agent_monitors_workspace_status_next_run_at' not in agent_monitor_indexes:
        op.create_index(
            'idx_agent_monitors_workspace_status_next_run_at',
            'agent_monitors',
            ['workspace_id', 'status', 'next_run_at'],
            unique=False,
        )

    agent_run_indexes = _existing_indexes('agent_runs')
    if 'ix_agent_runs_monitor_id' not in agent_run_indexes:
        op.create_index('ix_agent_runs_monitor_id', 'agent_runs', ['monitor_id'], unique=False)
    if 'ix_agent_runs_workspace_id' not in agent_run_indexes:
        op.create_index('ix_agent_runs_workspace_id', 'agent_runs', ['workspace_id'], unique=False)
    if 'ix_agent_runs_subject_id' not in agent_run_indexes:
        op.create_index('ix_agent_runs_subject_id', 'agent_runs', ['subject_id'], unique=False)
    if 'ix_agent_runs_previous_run_id' not in agent_run_indexes:
        op.create_index('ix_agent_runs_previous_run_id', 'agent_runs', ['previous_run_id'], unique=False)
    if 'ix_agent_runs_prompt_session_id' not in agent_run_indexes:
        op.create_index('ix_agent_runs_prompt_session_id', 'agent_runs', ['prompt_session_id'], unique=False)
    if 'ix_agent_runs_prompt_iteration_id' not in agent_run_indexes:
        op.create_index('ix_agent_runs_prompt_iteration_id', 'agent_runs', ['prompt_iteration_id'], unique=False)
    if 'ix_agent_runs_trigger_kind' not in agent_run_indexes:
        op.create_index('ix_agent_runs_trigger_kind', 'agent_runs', ['trigger_kind'], unique=False)
    if 'ix_agent_runs_run_status' not in agent_run_indexes:
        op.create_index('ix_agent_runs_run_status', 'agent_runs', ['run_status'], unique=False)
    if 'idx_agent_runs_monitor_started_at' not in agent_run_indexes:
        op.create_index(
            'idx_agent_runs_monitor_started_at',
            'agent_runs',
            ['monitor_id', 'started_at'],
            unique=False,
        )
    if 'idx_agent_runs_workspace_subject_started_at' not in agent_run_indexes:
        op.create_index(
            'idx_agent_runs_workspace_subject_started_at',
            'agent_runs',
            ['workspace_id', 'subject_id', 'started_at'],
            unique=False,
        )

    agent_alert_indexes = _existing_indexes('agent_alerts')
    if 'ix_agent_alerts_workspace_id' not in agent_alert_indexes:
        op.create_index('ix_agent_alerts_workspace_id', 'agent_alerts', ['workspace_id'], unique=False)
    if 'ix_agent_alerts_subject_id' not in agent_alert_indexes:
        op.create_index('ix_agent_alerts_subject_id', 'agent_alerts', ['subject_id'], unique=False)
    if 'ix_agent_alerts_run_id' not in agent_alert_indexes:
        op.create_index('ix_agent_alerts_run_id', 'agent_alerts', ['run_id'], unique=False)
    if 'ix_agent_alerts_severity' not in agent_alert_indexes:
        op.create_index('ix_agent_alerts_severity', 'agent_alerts', ['severity'], unique=False)
    if 'ix_agent_alerts_status' not in agent_alert_indexes:
        op.create_index('ix_agent_alerts_status', 'agent_alerts', ['status'], unique=False)
    if 'idx_agent_alerts_workspace_status_created_at' not in agent_alert_indexes:
        op.create_index(
            'idx_agent_alerts_workspace_status_created_at',
            'agent_alerts',
            ['workspace_id', 'status', 'created_at'],
            unique=False,
        )

    freshness_indexes = _existing_indexes('freshness_records')
    if 'ix_freshness_records_workspace_id' not in freshness_indexes:
        op.create_index('ix_freshness_records_workspace_id', 'freshness_records', ['workspace_id'], unique=False)
    if 'ix_freshness_records_subject_id' not in freshness_indexes:
        op.create_index('ix_freshness_records_subject_id', 'freshness_records', ['subject_id'], unique=False)
    if 'ix_freshness_records_source_id' not in freshness_indexes:
        op.create_index('ix_freshness_records_source_id', 'freshness_records', ['source_id'], unique=False)
    if 'ix_freshness_records_report_id' not in freshness_indexes:
        op.create_index('ix_freshness_records_report_id', 'freshness_records', ['report_id'], unique=False)
    if 'ix_freshness_records_status' not in freshness_indexes:
        op.create_index('ix_freshness_records_status', 'freshness_records', ['status'], unique=False)
    if 'idx_freshness_records_workspace_status_observed_at' not in freshness_indexes:
        op.create_index(
            'idx_freshness_records_workspace_status_observed_at',
            'freshness_records',
            ['workspace_id', 'status', 'observed_at'],
            unique=False,
        )

    if 'prompt_sessions' in tables:
        session_columns = _existing_columns('prompt_sessions')
        session_foreign_keys = _existing_foreign_keys('prompt_sessions')
        with op.batch_alter_table('prompt_sessions') as batch_op:
            if 'agent_monitor_id' not in session_columns:
                batch_op.add_column(sa.Column('agent_monitor_id', sa.String(length=36), nullable=True))
            if 'trigger_kind' not in session_columns:
                batch_op.add_column(sa.Column('trigger_kind', sa.String(length=40), nullable=True))
            if 'fk_prompt_sessions_agent_monitor_id' not in session_foreign_keys:
                batch_op.create_foreign_key(
                    'fk_prompt_sessions_agent_monitor_id',
                    'agent_monitors',
                    ['agent_monitor_id'],
                    ['id'],
                )

        session_indexes = _existing_indexes('prompt_sessions')
        if 'ix_prompt_sessions_agent_monitor_id' not in session_indexes:
            op.create_index(
                'ix_prompt_sessions_agent_monitor_id',
                'prompt_sessions',
                ['agent_monitor_id'],
                unique=False,
            )
        if 'ix_prompt_sessions_trigger_kind' not in session_indexes:
            op.create_index('ix_prompt_sessions_trigger_kind', 'prompt_sessions', ['trigger_kind'], unique=False)


def downgrade() -> None:
    tables = _existing_tables()

    if 'prompt_sessions' in tables:
        op.drop_index('ix_prompt_sessions_trigger_kind', table_name='prompt_sessions', if_exists=True)
        op.drop_index('ix_prompt_sessions_agent_monitor_id', table_name='prompt_sessions', if_exists=True)

        session_columns = _existing_columns('prompt_sessions')
        session_foreign_keys = _existing_foreign_keys('prompt_sessions')
        with op.batch_alter_table('prompt_sessions') as batch_op:
            if 'fk_prompt_sessions_agent_monitor_id' in session_foreign_keys:
                batch_op.drop_constraint('fk_prompt_sessions_agent_monitor_id', type_='foreignkey')
            if 'trigger_kind' in session_columns:
                batch_op.drop_column('trigger_kind')
            if 'agent_monitor_id' in session_columns:
                batch_op.drop_column('agent_monitor_id')

    if 'freshness_records' in tables:
        op.drop_index('idx_freshness_records_workspace_status_observed_at', table_name='freshness_records', if_exists=True)
        op.drop_index('ix_freshness_records_status', table_name='freshness_records', if_exists=True)
        op.drop_index('ix_freshness_records_report_id', table_name='freshness_records', if_exists=True)
        op.drop_index('ix_freshness_records_source_id', table_name='freshness_records', if_exists=True)
        op.drop_index('ix_freshness_records_subject_id', table_name='freshness_records', if_exists=True)
        op.drop_index('ix_freshness_records_workspace_id', table_name='freshness_records', if_exists=True)
        op.drop_table('freshness_records')

    if 'agent_alerts' in tables:
        op.drop_index('idx_agent_alerts_workspace_status_created_at', table_name='agent_alerts', if_exists=True)
        op.drop_index('ix_agent_alerts_status', table_name='agent_alerts', if_exists=True)
        op.drop_index('ix_agent_alerts_severity', table_name='agent_alerts', if_exists=True)
        op.drop_index('ix_agent_alerts_run_id', table_name='agent_alerts', if_exists=True)
        op.drop_index('ix_agent_alerts_subject_id', table_name='agent_alerts', if_exists=True)
        op.drop_index('ix_agent_alerts_workspace_id', table_name='agent_alerts', if_exists=True)
        op.drop_table('agent_alerts')

    if 'agent_runs' in tables:
        op.drop_index('idx_agent_runs_workspace_subject_started_at', table_name='agent_runs', if_exists=True)
        op.drop_index('idx_agent_runs_monitor_started_at', table_name='agent_runs', if_exists=True)
        op.drop_index('ix_agent_runs_run_status', table_name='agent_runs', if_exists=True)
        op.drop_index('ix_agent_runs_trigger_kind', table_name='agent_runs', if_exists=True)
        op.drop_index('ix_agent_runs_prompt_iteration_id', table_name='agent_runs', if_exists=True)
        op.drop_index('ix_agent_runs_prompt_session_id', table_name='agent_runs', if_exists=True)
        op.drop_index('ix_agent_runs_previous_run_id', table_name='agent_runs', if_exists=True)
        op.drop_index('ix_agent_runs_subject_id', table_name='agent_runs', if_exists=True)
        op.drop_index('ix_agent_runs_workspace_id', table_name='agent_runs', if_exists=True)
        op.drop_index('ix_agent_runs_monitor_id', table_name='agent_runs', if_exists=True)
        op.drop_table('agent_runs')

    if 'agent_monitors' in tables:
        op.drop_index('idx_agent_monitors_workspace_status_next_run_at', table_name='agent_monitors', if_exists=True)
        op.drop_index('ix_agent_monitors_status', table_name='agent_monitors', if_exists=True)
        op.drop_index('ix_agent_monitors_monitor_type', table_name='agent_monitors', if_exists=True)
        op.drop_index('ix_agent_monitors_workflow_recipe_version_id', table_name='agent_monitors', if_exists=True)
        op.drop_index('ix_agent_monitors_run_preset_id', table_name='agent_monitors', if_exists=True)
        op.drop_index('ix_agent_monitors_subject_id', table_name='agent_monitors', if_exists=True)
        op.drop_index('ix_agent_monitors_watchlist_id', table_name='agent_monitors', if_exists=True)
        op.drop_index('ix_agent_monitors_workspace_id', table_name='agent_monitors', if_exists=True)
        op.drop_index('ix_agent_monitors_user_id', table_name='agent_monitors', if_exists=True)
        op.drop_table('agent_monitors')

    if 'watchlist_items' in tables:
        op.drop_index('idx_watchlist_items_watchlist_sort_order', table_name='watchlist_items', if_exists=True)
        op.drop_index('ix_watchlist_items_subject_id', table_name='watchlist_items', if_exists=True)
        op.drop_index('ix_watchlist_items_watchlist_id', table_name='watchlist_items', if_exists=True)
        op.drop_table('watchlist_items')

    if 'watchlists' in tables:
        op.drop_index('idx_watchlists_workspace_updated_at', table_name='watchlists', if_exists=True)
        op.drop_index('ix_watchlists_workspace_id', table_name='watchlists', if_exists=True)
        op.drop_index('ix_watchlists_user_id', table_name='watchlists', if_exists=True)
        op.drop_table('watchlists')
