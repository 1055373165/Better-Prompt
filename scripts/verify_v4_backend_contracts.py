#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from verify_v2_stack import DEV_SCRIPT, ROOT_DIR, _candidate_ports, ensure, http_request


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def wait_for_v4_backend() -> tuple[int, bool]:
    started_here = False

    discovered = discover_healthy_v4_backend()
    if discovered is not None:
        return discovered, started_here

    subprocess.run([str(DEV_SCRIPT), 'start'], cwd=ROOT_DIR, check=True)
    started_here = True

    for _ in range(20):
        discovered = discover_healthy_v4_backend()
        if discovered is not None:
            return discovered, started_here
        time.sleep(1)

    raise RuntimeError('local V4 backend did not become healthy in time')


def discover_healthy_v4_backend() -> int | None:
    for port in _candidate_ports('BETTERPROMPT_VERIFY_BACKEND_PORT', 'backend', [8000, 8001, 8002, 8003]):
        try:
            backend_health = http_request('GET', f'http://127.0.0.1:{port}/api/v1/health', timeout=2.0)
            monitor_list = http_request(
                'GET',
                f'http://127.0.0.1:{port}/api/v1/agent-monitors?page=1&page_size=1',
                timeout=2.0,
            )
        except RuntimeError:
            continue
        if (
            isinstance(backend_health, dict)
            and backend_health.get('status') == 'ok'
            and isinstance(monitor_list, dict)
            and isinstance(monitor_list.get('items'), list)
        ):
            return port
    return None


def run_http_smoke(backend_port: int) -> dict[str, str]:
    backend_base = f'http://127.0.0.1:{backend_port}/api/v1'
    smoke_suffix = str(int(time.time() * 1000))

    workspace = http_request(
        'POST',
        f'{backend_base}/domain-workspaces',
        payload={
            'workspace_type': 'agent_runtime_verify',
            'name': f'V4 Runtime Workspace {smoke_suffix}',
            'description': 'Created by verify_v4_backend_contracts.py',
            'config': {},
        },
    )
    subject = http_request(
        'POST',
        f"{backend_base}/domain-workspaces/{workspace['id']}/subjects",
        payload={
            'subject_type': 'ticker',
            'external_key': f'v4-runtime-{smoke_suffix}',
            'display_name': f'Runtime Subject {smoke_suffix}',
            'metadata': {
                'created_by': 'verify_v4_backend_contracts',
                'focus': 'agent runtime contract verification',
            },
        },
    )
    source = http_request(
        'POST',
        f"{backend_base}/domain-workspaces/{workspace['id']}/sources",
        payload={
            'subject_id': subject['id'],
            'source_type': 'note',
            'title': f'Runtime Source {smoke_suffix}',
            'canonical_uri': f'https://example.com/v4-runtime/{smoke_suffix}',
            'content': {
                'summary': 'Source for runtime contract verification',
            },
        },
    )
    workflow_recipe = http_request(
        'POST',
        f'{backend_base}/workflow-recipes',
        payload={
            'name': f'V4 Runtime Recipe {smoke_suffix}',
            'description': 'Created by verify_v4_backend_contracts.py',
            'definition': {
                'steps': [
                    {'mode': 'generate', 'label': 'baseline rerun'},
                ],
            },
        },
    )
    run_preset = http_request(
        'POST',
        f'{backend_base}/run-presets',
        payload={
            'name': f'V4 Runtime Preset {smoke_suffix}',
            'description': 'Created by verify_v4_backend_contracts.py',
            'definition': {
                'mode': 'debug',
                'workflow_recipe_version_id': workflow_recipe['current_version']['id'],
                'run_settings': {
                    'original_task': 'Review the latest monitored update',
                    'current_prompt': 'Please summarize the latest monitored update.',
                    'current_output': 'Looks good overall.',
                },
            },
        },
    )

    watchlist = http_request(
        'POST',
        f'{backend_base}/watchlists',
        payload={
            'workspace_id': workspace['id'],
            'name': f'Core Watchlist {smoke_suffix}',
            'description': 'Created by V4 backend contract verify script',
        },
    )
    updated_watchlist = http_request(
        'PATCH',
        f"{backend_base}/watchlists/{watchlist['id']}",
        payload={
            'description': 'Updated by V4 backend contract verify script',
        },
    )
    watchlist_item = http_request(
        'POST',
        f"{backend_base}/watchlists/{watchlist['id']}/items",
        payload={
            'subject_id': subject['id'],
        },
    )
    watchlist_items = http_request('GET', f"{backend_base}/watchlists/{watchlist['id']}/items")
    watchlists = http_request(
        'GET',
        f"{backend_base}/watchlists?{urlencode({'workspace_id': workspace['id']})}",
    )

    next_run_at = (_utcnow() + timedelta(days=1)).replace(microsecond=0).isoformat()
    monitor = http_request(
        'POST',
        f'{backend_base}/agent-monitors',
        payload={
            'workspace_id': workspace['id'],
            'watchlist_id': watchlist['id'],
            'subject_id': subject['id'],
            'run_preset_id': run_preset['id'],
            'workflow_recipe_version_id': workflow_recipe['current_version']['id'],
            'monitor_type': 'schedule',
            'trigger_config': {'cadence': 'daily'},
            'alert_policy': {'only_material_change': True},
        },
    )
    updated_monitor = http_request(
        'PATCH',
        f"{backend_base}/agent-monitors/{monitor['id']}",
        payload={
            'next_run_at': next_run_at,
            'alert_policy': {'only_material_change': False},
        },
    )
    listed_monitors = http_request(
        'GET',
        f"{backend_base}/agent-monitors?{urlencode({'workspace_id': workspace['id'], 'subject_id': subject['id']})}",
    )
    first_run = http_request('POST', f"{backend_base}/agent-monitors/{monitor['id']}/trigger")
    second_run = http_request('POST', f"{backend_base}/agent-monitors/{monitor['id']}/trigger")
    listed_runs = http_request('GET', f"{backend_base}/agent-monitors/{monitor['id']}/runs")
    run_detail = http_request('GET', f"{backend_base}/agent-runs/{second_run['id']}")

    session_query = urlencode(
        {
            'run_kind': 'agent_run',
            'domain_workspace_id': workspace['id'],
            'subject_id': subject['id'],
            'agent_monitor_id': monitor['id'],
            'trigger_kind': 'manual',
        }
    )
    sessions = http_request('GET', f'{backend_base}/prompt-sessions?{session_query}')
    session_detail = http_request('GET', f"{backend_base}/prompt-sessions/{first_run['prompt_session_id']}")
    alerts = http_request(
        'GET',
        f"{backend_base}/agent-alerts?{urlencode({'workspace_id': workspace['id'], 'subject_id': subject['id']})}",
    )
    freshness = http_request(
        'GET',
        f"{backend_base}/freshness-records?{urlencode({'workspace_id': workspace['id'], 'subject_id': subject['id'], 'source_id': source['id']})}",
    )

    ensure(updated_watchlist['description'] == 'Updated by V4 backend contract verify script', 'watchlist patch failed')
    ensure(watchlist_item['subject_id'] == subject['id'], 'watchlist item should preserve subject_id')
    ensure(len(watchlist_items['items']) == 1, 'watchlist items should include created item')
    ensure(watchlists['items'][0]['id'] == watchlist['id'], 'watchlist list should include created watchlist')

    ensure(updated_monitor['next_run_at'] == next_run_at, 'monitor patch should preserve next_run_at')
    ensure(updated_monitor['alert_policy']['only_material_change'] is False, 'monitor patch should update alert_policy')
    ensure(listed_monitors['items'][0]['id'] == monitor['id'], 'monitor list should include created monitor')
    ensure(first_run['run_status'] == 'completed', 'first monitor trigger should execute a completed run')
    ensure(first_run['prompt_session_id'], 'first monitor trigger should create prompt_session provenance')
    ensure(first_run['prompt_iteration_id'], 'first monitor trigger should create prompt_iteration provenance')
    ensure(second_run['previous_run_id'] == first_run['id'], 'second monitor trigger should link previous_run_id')
    ensure([item['id'] for item in listed_runs['items']] == [second_run['id'], first_run['id']], 'monitor runs should be newest-first')
    ensure(run_detail['id'] == second_run['id'], 'agent run detail should return the requested run')
    ensure(run_detail['change_summary']['state'] == 'completed', 'run detail should expose completed change summary')
    ensure(run_detail['prompt_iteration_id'], 'run detail should expose prompt_iteration_id')

    matching_session = next((item for item in sessions['items'] if item['id'] == first_run['prompt_session_id']), None)
    ensure(matching_session is not None, 'prompt-sessions should include the triggered agent session')
    ensure(matching_session['agent_monitor_id'] == monitor['id'], 'session summary should preserve agent_monitor_id')
    ensure(matching_session['run_preset_id'] == run_preset['id'], 'session summary should preserve run_preset_id')
    ensure(
        matching_session['workflow_recipe_version_id'] == workflow_recipe['current_version']['id'],
        'session summary should preserve workflow recipe version',
    )
    ensure(session_detail['run_kind'] == 'agent_run', 'session detail should preserve agent_run')
    ensure(session_detail['trigger_kind'] == 'manual', 'session detail should preserve trigger_kind')
    ensure(session_detail['agent_monitor_id'] == monitor['id'], 'session detail should preserve agent_monitor_id')

    ensure(isinstance(alerts.get('items'), list), 'agent-alerts should return a list response')
    ensure(isinstance(freshness.get('items'), list), 'freshness-records should return a list response')

    return {
        'workspace_id': workspace['id'],
        'subject_id': subject['id'],
        'watchlist_id': watchlist['id'],
        'monitor_id': monitor['id'],
        'run_id': second_run['id'],
        'session_id': first_run['prompt_session_id'],
    }


def main() -> None:
    backend_port, started_here = wait_for_v4_backend()
    try:
        results = run_http_smoke(backend_port)
        print('v4 backend contract verification passed')
        print(f'backend=http://127.0.0.1:{backend_port}')
        print(f"workspace_id={results['workspace_id']}")
        print(f"subject_id={results['subject_id']}")
        print(f"watchlist_id={results['watchlist_id']}")
        print(f"monitor_id={results['monitor_id']}")
        print(f"run_id={results['run_id']}")
        print(f"session_id={results['session_id']}")
    finally:
        if started_here:
            subprocess.run([str(DEV_SCRIPT), 'stop'], cwd=ROOT_DIR, check=False)


if __name__ == '__main__':
    main()
