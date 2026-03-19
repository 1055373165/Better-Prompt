#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / 'betterprompt'
PORTS_FILE = APP_DIR / '.run' / 'dev-ports.env'
DEV_SCRIPT = ROOT_DIR / 'scripts' / 'betterprompt-dev.sh'


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_runtime_ports() -> dict[str, int]:
    ensure(PORTS_FILE.exists(), f'missing runtime ports file: {PORTS_FILE}')
    raw_values: dict[str, str] = {}
    for line in PORTS_FILE.read_text(encoding='utf-8').splitlines():
        stripped = line.strip()
        if not stripped or '=' not in stripped:
            continue
        key, value = stripped.split('=', 1)
        raw_values[key.strip()] = value.strip()

    try:
        return {
            'backend': int(raw_values['BACKEND_PORT']),
            'frontend': int(raw_values['FRONTEND_PORT']),
        }
    except (KeyError, ValueError) as exc:
        raise RuntimeError(f'invalid runtime ports file: {PORTS_FILE}') from exc


def http_request(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: float = 15.0,
) -> Any:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    request = Request(url=url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return json.loads(body.decode('utf-8'))
            return body.decode('utf-8')
    except HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'{method} {url} failed with {exc.code}: {detail}') from exc
    except URLError as exc:
        raise RuntimeError(f'{method} {url} failed: {exc.reason}') from exc
    except TimeoutError as exc:
        raise RuntimeError(f'{method} {url} failed: timed out') from exc


def wait_for_stack() -> tuple[dict[str, int], bool]:
    started_here = False

    discovered = discover_healthy_stack()
    if discovered is not None:
        return discovered, started_here

    if not _stack_is_healthy():
        subprocess.run([str(DEV_SCRIPT), 'start'], cwd=ROOT_DIR, check=True)
        started_here = True

    for _ in range(20):
        discovered = discover_healthy_stack()
        if discovered is not None:
            return discovered, started_here
        time.sleep(1)

    raise RuntimeError('local dev stack did not become healthy in time')


def _stack_is_healthy() -> bool:
    return discover_healthy_stack() is not None


def discover_healthy_stack() -> dict[str, int] | None:
    backend_port = _find_healthy_backend_port()
    frontend_port = _find_healthy_frontend_port()
    if backend_port is None or frontend_port is None:
        return None
    return {
        'backend': backend_port,
        'frontend': frontend_port,
    }


def _find_healthy_backend_port() -> int | None:
    for port in _candidate_ports('BETTERPROMPT_VERIFY_BACKEND_PORT', 'backend', [8000, 8001, 8002, 8003]):
        try:
            backend_health = http_request('GET', f'http://127.0.0.1:{port}/api/v1/health', timeout=2.0)
            context_pack_list = http_request(
                'GET',
                f'http://127.0.0.1:{port}/api/v1/context-packs?page=1&page_size=1',
                timeout=2.0,
            )
        except RuntimeError:
            continue
        if (
            isinstance(backend_health, dict)
            and backend_health.get('status') == 'ok'
            and isinstance(context_pack_list, dict)
            and isinstance(context_pack_list.get('items'), list)
        ):
            return port
    return None


def _find_healthy_frontend_port() -> int | None:
    for port in _candidate_ports('BETTERPROMPT_VERIFY_FRONTEND_PORT', 'frontend', [5173, 5174, 5175, 5176]):
        try:
            frontend_html = http_request('GET', f'http://127.0.0.1:{port}', timeout=2.0)
        except RuntimeError:
            continue
        if isinstance(frontend_html, str) and '<!doctype html>' in frontend_html.lower():
            return port
    return None


def _candidate_ports(env_name: str, runtime_key: str, defaults: list[int]) -> list[int]:
    values: list[int] = []

    env_value = os.getenv(env_name)
    if env_value:
        try:
            values.append(int(env_value))
        except ValueError:
            raise RuntimeError(f'{env_name} must be an integer port, got: {env_value}') from None

    if PORTS_FILE.exists():
        try:
            runtime_ports = load_runtime_ports()
        except RuntimeError:
            runtime_ports = {}
        runtime_port = runtime_ports.get(runtime_key)
        if isinstance(runtime_port, int):
            values.append(runtime_port)

    values.extend(defaults)

    deduped: list[int] = []
    seen: set[int] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def run_http_smoke(ports: dict[str, int]) -> dict[str, str]:
    backend_base = f"http://127.0.0.1:{ports['backend']}/api/v1"
    smoke_suffix = str(int(time.time() * 1000))

    context_pack = http_request(
        'POST',
        f'{backend_base}/context-packs',
        payload={
            'name': f'HTTP Smoke Context Pack {smoke_suffix}',
            'description': 'Created by verify_v2_stack.py',
            'payload': {
                'brief': 'Regression smoke',
                'constraints': ['keep acceptance criteria explicit', 'preserve provenance'],
            },
            'tags': ['smoke', 'http'],
        },
    )
    evaluation_profile = http_request(
        'POST',
        f'{backend_base}/evaluation-profiles',
        payload={
            'name': f'HTTP Smoke Evaluation Profile {smoke_suffix}',
            'description': 'Created by verify_v2_stack.py',
            'rules': {
                'weights': {'clarity': 5, 'execution': 5},
                'notes': 'Prefer actionable review guidance',
            },
        },
    )
    workflow_recipe = http_request(
        'POST',
        f'{backend_base}/workflow-recipes',
        payload={
            'name': f'HTTP Smoke Workflow Recipe {smoke_suffix}',
            'description': 'Created by verify_v2_stack.py',
            'domain_hint': 'code-review',
            'definition': {
                'steps': [
                    {'mode': 'debug', 'label': 'repair shallow review prompt'},
                ],
            },
        },
    )
    run_preset = http_request(
        'POST',
        f'{backend_base}/run-presets',
        payload={
            'name': f'HTTP Smoke Debug Preset {smoke_suffix}',
            'description': 'Created by verify_v2_stack.py',
            'definition': {
                'mode': 'debug',
                'context_pack_version_ids': [context_pack['current_version']['id']],
                'evaluation_profile_version_id': evaluation_profile['current_version']['id'],
                'workflow_recipe_version_id': workflow_recipe['current_version']['id'],
                'run_settings': {
                    'original_task': 'Review this API design prompt',
                    'current_prompt': 'Please review the design and tell me if it looks good.',
                    'current_output': 'Looks good overall.',
                    'output_preference': 'balanced',
                },
            },
        },
    )
    launch_response = http_request(
        'POST',
        f"{backend_base}/run-presets/{run_preset['id']}/launch",
        payload={},
    )

    ensure(launch_response['mode'] == 'debug', 'launch should execute the preset in debug mode')
    ensure(launch_response['iteration']['session_id'], 'launch should persist session_id')
    ensure(launch_response['iteration']['iteration_id'], 'launch should persist iteration_id')
    ensure(launch_response['fixed_prompt'], 'debug launch should return a fixed_prompt')

    query = urlencode(
        {
            'run_kind': 'preset_run',
            'run_preset_id': run_preset['id'],
            'workflow_recipe_version_id': workflow_recipe['current_version']['id'],
        }
    )
    sessions = http_request('GET', f'{backend_base}/prompt-sessions?{query}')
    matching_summary = next(
        (item for item in sessions['items'] if item['id'] == launch_response['iteration']['session_id']),
        None,
    )
    ensure(matching_summary is not None, 'session list should include the launched preset session')
    ensure(matching_summary['run_preset_name'] == run_preset['name'], 'session summary should expose preset name')
    ensure(
        matching_summary['workflow_recipe_name'] == workflow_recipe['name'],
        'session summary should expose workflow recipe name',
    )

    session_detail = http_request(
        'GET',
        f"{backend_base}/prompt-sessions/{launch_response['iteration']['session_id']}",
    )
    ensure(session_detail['run_preset_name'] == run_preset['name'], 'session detail should expose preset name')
    ensure(
        session_detail['workflow_recipe_version_id'] == workflow_recipe['current_version']['id'],
        'session detail should preserve workflow recipe provenance',
    )

    return {
        'run_preset_id': run_preset['id'],
        'session_id': launch_response['iteration']['session_id'],
        'iteration_id': launch_response['iteration']['iteration_id'],
    }


def main() -> None:
    ports, started_here = wait_for_stack()
    try:
        results = run_http_smoke(ports)
        print('v2 full-stack verification passed')
        print(f"frontend=http://127.0.0.1:{ports['frontend']}")
        print(f"backend=http://127.0.0.1:{ports['backend']}")
        print(f"run_preset_id={results['run_preset_id']}")
        print(f"session_id={results['session_id']}")
        print(f"iteration_id={results['iteration_id']}")
    finally:
        if started_here:
            subprocess.run([str(DEV_SCRIPT), 'stop'], cwd=ROOT_DIR, check=False)


if __name__ == '__main__':
    main()
