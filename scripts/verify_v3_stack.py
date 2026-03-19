#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import time
from urllib.parse import urlencode

from verify_v2_stack import DEV_SCRIPT, ROOT_DIR, _candidate_ports, ensure, http_request


def wait_for_v3_stack() -> tuple[dict[str, int], bool]:
    started_here = False

    discovered = discover_healthy_v3_stack()
    if discovered is not None:
        return discovered, started_here

    subprocess.run([str(DEV_SCRIPT), 'start'], cwd=ROOT_DIR, check=True)
    started_here = True

    for _ in range(20):
        discovered = discover_healthy_v3_stack()
        if discovered is not None:
            return discovered, started_here
        time.sleep(1)

    raise RuntimeError('local V3 dev stack did not become healthy in time')


def discover_healthy_v3_stack() -> dict[str, int] | None:
    backend_port = _find_v3_backend_port()
    frontend_port = _find_v3_frontend_port()
    if backend_port is None or frontend_port is None:
        return None
    return {
        'backend': backend_port,
        'frontend': frontend_port,
    }


def _find_v3_backend_port() -> int | None:
    for port in _candidate_ports('BETTERPROMPT_VERIFY_BACKEND_PORT', 'backend', [8000, 8001, 8002, 8003]):
        try:
            backend_health = http_request('GET', f'http://127.0.0.1:{port}/api/v1/health', timeout=2.0)
            workspace_list = http_request(
                'GET',
                f'http://127.0.0.1:{port}/api/v1/domain-workspaces?page=1&page_size=1',
                timeout=2.0,
            )
        except RuntimeError:
            continue
        if (
            isinstance(backend_health, dict)
            and backend_health.get('status') == 'ok'
            and isinstance(workspace_list, dict)
            and isinstance(workspace_list.get('items'), list)
        ):
            return port
    return None


def _find_v3_frontend_port() -> int | None:
    for port in _candidate_ports('BETTERPROMPT_VERIFY_FRONTEND_PORT', 'frontend', [5173, 5174, 5175, 5176, 5177]):
        try:
            frontend_html = http_request('GET', f'http://127.0.0.1:{port}/workspaces', timeout=2.0)
        except RuntimeError:
            continue
        if isinstance(frontend_html, str) and '<!doctype html>' in frontend_html.lower():
            return port
    return None


def run_http_smoke(ports: dict[str, int]) -> dict[str, str]:
    backend_base = f"http://127.0.0.1:{ports['backend']}/api/v1"
    frontend_base = f"http://127.0.0.1:{ports['frontend']}"
    smoke_suffix = str(int(time.time() * 1000))

    workspace = http_request(
        'POST',
        f'{backend_base}/domain-workspaces',
        payload={
            'workspace_type': 'workspace_verify',
            'name': f'HTTP Workspace {smoke_suffix}',
            'description': 'Created by verify_v3_stack.py',
            'config': {},
        },
    )
    subject = http_request(
        'POST',
        f"{backend_base}/domain-workspaces/{workspace['id']}/subjects",
        payload={
            'subject_type': 'topic',
            'external_key': f'workspace-topic-{smoke_suffix}',
            'display_name': f'Workspace Subject {smoke_suffix}',
            'metadata': {
                'created_by': 'verify_v3_stack',
                'focus': 'workspace provenance regression',
            },
        },
    )
    source = http_request(
        'POST',
        f"{backend_base}/domain-workspaces/{workspace['id']}/sources",
        payload={
            'subject_id': subject['id'],
            'source_type': 'note',
            'title': f'Workspace Source {smoke_suffix}',
            'canonical_uri': f'https://example.com/workspace-smoke/{smoke_suffix}',
            'content': {
                'summary': 'Workspace source created by full-stack verify script',
                'checks': ['workspace list', 'subject scoping', 'report provenance'],
            },
        },
    )
    report = http_request(
        'POST',
        f"{backend_base}/domain-workspaces/{workspace['id']}/reports",
        payload={
            'subject_id': subject['id'],
            'report_type': 'workspace_brief',
            'title': f'Workspace Report {smoke_suffix}',
            'content': {
                'thesis': 'Initial workspace report',
                'source_uri': source['canonical_uri'],
            },
            'summary_text': 'v1',
            'confidence_score': 0.61,
        },
    )
    updated_report = http_request(
        'POST',
        f"{backend_base}/research-reports/{report['id']}/versions",
        payload={
            'content': {
                'thesis': 'Refined workspace report',
                'source_uri': source['canonical_uri'],
                'notes': ['second pass'],
            },
            'summary_text': 'v2',
            'confidence_score': 0.84,
        },
    )

    ensure(updated_report['latest_version']['version_number'] == 2, 'report version should increment to v2')

    workspace_detail = http_request('GET', f"{backend_base}/domain-workspaces/{workspace['id']}")
    ensure(workspace_detail['subject_count'] == 1, 'workspace detail should expose subject count')
    ensure(workspace_detail['source_count'] == 1, 'workspace detail should expose source count')
    ensure(workspace_detail['report_count'] == 1, 'workspace detail should expose report count')

    subjects = http_request('GET', f"{backend_base}/domain-workspaces/{workspace['id']}/subjects")
    ensure(len(subjects['items']) == 1, 'workspace subject list should include the created subject')
    ensure(subjects['items'][0]['id'] == subject['id'], 'subject list should return the created subject first')

    sources = http_request(
        'GET',
        f"{backend_base}/domain-workspaces/{workspace['id']}/sources?{urlencode({'subject_id': subject['id']})}",
    )
    ensure(len(sources['items']) == 1, 'workspace source list should include the created source')
    ensure(sources['items'][0]['id'] == source['id'], 'source list should return the created source')

    reports = http_request(
        'GET',
        f"{backend_base}/domain-workspaces/{workspace['id']}/reports?{urlencode({'subject_id': subject['id']})}",
    )
    ensure(len(reports['items']) == 1, 'workspace report list should include the created report')
    ensure(
        reports['items'][0]['latest_version']['version_number'] == 2,
        'report list should surface the refined latest version',
    )

    versions = http_request('GET', f"{backend_base}/research-reports/{report['id']}/versions")
    ensure(
        [item['version_number'] for item in versions['items']] == [2, 1],
        'report versions should be returned newest-first',
    )

    debug_response = http_request(
        'POST',
        f'{backend_base}/prompt-agent/debug',
        payload={
            'original_task': 'Diagnose why the workspace prompt is too shallow',
            'current_prompt': 'Please analyze this topic.',
            'current_output': 'Looks good overall.',
            'domain_workspace_id': workspace['id'],
            'subject_id': subject['id'],
        },
    )
    ensure(debug_response['mode'] == 'debug', 'workspace debug should return debug mode')
    ensure(debug_response['iteration']['session_id'], 'workspace debug should persist session_id')
    ensure(debug_response['iteration']['iteration_id'], 'workspace debug should persist iteration_id')
    ensure(debug_response['fixed_prompt'], 'workspace debug should return a fixed_prompt')

    session_query = urlencode(
        {
            'run_kind': 'workspace_run',
            'domain_workspace_id': workspace['id'],
            'subject_id': subject['id'],
        }
    )
    sessions = http_request('GET', f'{backend_base}/prompt-sessions?{session_query}')
    matching_summary = next(
        (item for item in sessions['items'] if item['id'] == debug_response['iteration']['session_id']),
        None,
    )
    ensure(matching_summary is not None, 'session list should include the workspace debug session')
    ensure(matching_summary['run_kind'] == 'workspace_run', 'session summary should preserve workspace_run')
    ensure(
        matching_summary['domain_workspace_id'] == workspace['id'],
        'session summary should preserve domain_workspace_id',
    )
    ensure(matching_summary['subject_id'] == subject['id'], 'session summary should preserve subject_id')

    session_detail = http_request(
        'GET',
        f"{backend_base}/prompt-sessions/{debug_response['iteration']['session_id']}",
    )
    ensure(session_detail['run_kind'] == 'workspace_run', 'session detail should preserve workspace_run')
    ensure(
        session_detail['domain_workspace_id'] == workspace['id'],
        'session detail should preserve domain_workspace_id',
    )
    ensure(session_detail['subject_id'] == subject['id'], 'session detail should preserve subject_id')

    workspace_query = urlencode(
        {
            'workspace_id': workspace['id'],
            'subject_id': subject['id'],
        }
    )
    workbench_query = urlencode(
        {
            'workspace_id': workspace['id'],
            'subject_id': subject['id'],
            'workspace_name': workspace['name'],
            'subject_name': subject['display_name'],
        }
    )
    sessions_query = urlencode(
        {
            'run_kind': 'workspace_run',
            'domain_workspace_id': workspace['id'],
            'subject_id': subject['id'],
        }
    )

    workspaces_html = http_request('GET', f'{frontend_base}/workspaces?{workspace_query}')
    ensure('<!doctype html>' in workspaces_html.lower(), 'frontend should serve /workspaces')
    prompt_agent_html = http_request('GET', f'{frontend_base}/prompt-agent?{workbench_query}')
    ensure('<!doctype html>' in prompt_agent_html.lower(), 'frontend should serve /prompt-agent workspace deeplink')
    sessions_html = http_request('GET', f'{frontend_base}/sessions?{sessions_query}')
    ensure('<!doctype html>' in sessions_html.lower(), 'frontend should serve /sessions workspace filter deeplink')

    return {
        'workspace_id': workspace['id'],
        'subject_id': subject['id'],
        'report_id': report['id'],
        'session_id': debug_response['iteration']['session_id'],
        'iteration_id': debug_response['iteration']['iteration_id'],
    }


def main() -> None:
    ports, started_here = wait_for_v3_stack()
    try:
        results = run_http_smoke(ports)
        print('v3 full-stack verification passed')
        print(f"frontend=http://127.0.0.1:{ports['frontend']}")
        print(f"backend=http://127.0.0.1:{ports['backend']}")
        print(f"workspace_id={results['workspace_id']}")
        print(f"subject_id={results['subject_id']}")
        print(f"report_id={results['report_id']}")
        print(f"session_id={results['session_id']}")
        print(f"iteration_id={results['iteration_id']}")
    finally:
        if started_here:
            subprocess.run([str(DEV_SCRIPT), 'stop'], cwd=ROOT_DIR, check=False)


if __name__ == '__main__':
    main()
