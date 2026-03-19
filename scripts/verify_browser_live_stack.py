#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
from html.parser import HTMLParser
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import websockets

from verify_v2_stack import DEV_SCRIPT, ROOT_DIR, _candidate_ports, ensure, http_request
from verify_v3_stack import run_http_smoke as run_v3_http_smoke
from verify_v4_backend_contracts import run_http_smoke as run_v4_http_smoke


BROWSER_CANDIDATES = (
    Path('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),
    Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._current_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != 'a':
            return
        self._current_href = dict(attrs).get('href')
        self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != 'a' or self._current_href is None:
            return
        text = normalize_text(''.join(self._current_text))
        if text:
            self.links.append((text, self._current_href))
        self._current_href = None
        self._current_text = []


def normalize_text(value: str) -> str:
    return ' '.join(value.split())


def browser_binary() -> str:
    override = os.getenv('BETTERPROMPT_BROWSER_BIN')
    if override:
        ensure(Path(override).exists(), f'BETTERPROMPT_BROWSER_BIN does not exist: {override}')
        return override

    for candidate in BROWSER_CANDIDATES:
        if candidate.exists():
            return str(candidate)

    raise RuntimeError('No supported browser binary found. Set BETTERPROMPT_BROWSER_BIN to Chrome or Edge.')


def discover_browser_stack() -> dict[str, int] | None:
    frontend_port = _find_frontend_port()
    if frontend_port is None:
        return None

    for port in _candidate_ports('BETTERPROMPT_VERIFY_BACKEND_PORT', 'backend', [8000, 8001, 8002, 8003]):
        try:
            backend_health = http_request('GET', f'http://127.0.0.1:{port}/api/v1/health', timeout=2.0)
            workspace_list = http_request(
                'GET',
                f'http://127.0.0.1:{port}/api/v1/domain-workspaces?page=1&page_size=1',
                timeout=2.0,
            )
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
            and isinstance(workspace_list, dict)
            and isinstance(workspace_list.get('items'), list)
            and isinstance(monitor_list, dict)
            and isinstance(monitor_list.get('items'), list)
        ):
            return {
                'backend': port,
                'frontend': frontend_port,
            }
    return None


def _find_frontend_port() -> int | None:
    for port in _candidate_ports('BETTERPROMPT_VERIFY_FRONTEND_PORT', 'frontend', [5173, 5174, 5175, 5176, 5177]):
        try:
            frontend_html = http_request('GET', f'http://127.0.0.1:{port}/workspaces', timeout=2.0)
        except RuntimeError:
            continue
        if isinstance(frontend_html, str) and '<!doctype html>' in frontend_html.lower():
            return port
    return None


def wait_for_browser_stack() -> tuple[dict[str, int], bool]:
    started_here = False

    discovered = discover_browser_stack()
    if discovered is not None:
        return discovered, started_here

    subprocess.run([str(DEV_SCRIPT), 'start'], cwd=ROOT_DIR, check=True)
    started_here = True

    for _ in range(20):
        discovered = discover_browser_stack()
        if discovered is not None:
            return discovered, started_here
        time.sleep(1)

    raise RuntimeError('local browser verification stack did not become healthy in time')


def _reserve_debug_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return int(sock.getsockname()[1])


class CDPSession:
    def __init__(self, websocket) -> None:
        self.websocket = websocket
        self._message_id = 0

    async def call(self, method: str, params: dict[str, object] | None = None) -> dict[str, object]:
        self._message_id += 1
        message_id = self._message_id
        await self.websocket.send(
            json.dumps(
                {
                    'id': message_id,
                    'method': method,
                    'params': params or {},
                }
            )
        )

        while True:
            raw_message = await self.websocket.recv()
            message = json.loads(raw_message)
            if message.get('id') != message_id:
                continue
            if 'error' in message:
                raise RuntimeError(f'CDP {method} failed: {message["error"]}')
            return message.get('result', {})

    async def evaluate_string(self, expression: str) -> str:
        result = await self.call(
            'Runtime.evaluate',
            {
                'expression': expression,
                'returnByValue': True,
            },
        )
        remote_result = result.get('result', {})
        value = remote_result.get('value', '')
        return value if isinstance(value, str) else ''

    async def wait_for_texts(self, texts: list[str], timeout_seconds: float = 40.0) -> tuple[str, str]:
        deadline = time.time() + timeout_seconds
        last_body_text = ''

        while time.time() < deadline:
            ready_state = await self.evaluate_string('document.readyState')
            body_text = await self.evaluate_string("document.body ? document.body.innerText : ''")
            last_body_text = body_text
            if ready_state == 'complete' and all(text in body_text for text in texts):
                html = await self.evaluate_string('document.documentElement.outerHTML')
                return html, body_text
            await asyncio.sleep(1)

        missing = [text for text in texts if text not in last_body_text]
        preview = normalize_text(last_body_text)[:400]
        raise AssertionError(f'page did not render expected content. Missing: {missing}. Body preview: {preview!r}')


async def _capture_page_state(url: str, expected_texts: list[str]) -> tuple[str, str]:
    debug_port = _reserve_debug_port()
    with tempfile.TemporaryDirectory(prefix='betterprompt-browser-smoke-') as user_data_dir:
        process = subprocess.Popen(
            [
                browser_binary(),
                '--headless=new',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-sync',
                '--disable-component-update',
                '--no-first-run',
                '--no-default-browser-check',
                f'--user-data-dir={user_data_dir}',
                '--window-size=1440,2200',
                f'--remote-debugging-port={debug_port}',
                'about:blank',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            version_payload = None
            for _ in range(20):
                try:
                    version_payload = http_request('GET', f'http://127.0.0.1:{debug_port}/json/version', timeout=1.0)
                except RuntimeError:
                    time.sleep(0.5)
                    continue
                if isinstance(version_payload, dict):
                    break
            ensure(isinstance(version_payload, dict), f'CDP debugger did not become ready on port {debug_port}')

            targets = http_request('GET', f'http://127.0.0.1:{debug_port}/json/list', timeout=1.0)
            ensure(isinstance(targets, list), 'CDP target list should be a JSON array')
            page_target = next(
                (target for target in targets if target.get('type') == 'page' and target.get('webSocketDebuggerUrl')),
                None,
            )
            ensure(page_target is not None, 'CDP should expose at least one page target')
            websocket_url = page_target['webSocketDebuggerUrl']

            async with websockets.connect(websocket_url, max_size=None) as websocket:
                session = CDPSession(websocket)
                await session.call('Page.enable')
                await session.call('Runtime.enable')
                await session.call('Page.navigate', {'url': url})
                return await session.wait_for_texts(expected_texts)
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def capture_page_state(url: str, *, expected_texts: list[str]) -> tuple[str, str]:
    return asyncio.run(_capture_page_state(url, expected_texts))


def find_link_href(dom: str, link_text: str) -> str | None:
    parser = LinkParser()
    parser.feed(dom)
    expected = normalize_text(link_text)
    for text, href in parser.links:
        if text == expected:
            return href
    return None


def ensure_query_value(href: str, key: str, expected: str) -> None:
    values = parse_qs(urlparse(href).query).get(key, [])
    ensure(values == [expected], f'{href} should contain {key}={expected}')


def run_v3_browser_smoke(ports: dict[str, int], v3_results: dict[str, str]) -> dict[str, str]:
    frontend_base = f"http://127.0.0.1:{ports['frontend']}"
    workspace_params = {
        'workspace_id': v3_results['workspace_id'],
        'subject_id': v3_results['subject_id'],
    }

    workspace_url = (
        f"{frontend_base}/workspaces?"
        f'{urlencode(workspace_params)}'
    )
    workspaces_dom, _ = capture_page_state(
        workspace_url,
        expected_texts=['查看 Workspace Sessions', '查看最新版本来源 Session'],
    )
    latest_session_href = find_link_href(workspaces_dom, '查看最新版本来源 Session')
    ensure(latest_session_href is not None, 'workspace page should expose latest version source session link')
    ensure_query_value(latest_session_href, 'domain_workspace_id', v3_results['workspace_id'])
    ensure_query_value(latest_session_href, 'subject_id', v3_results['subject_id'])
    ensure_query_value(latest_session_href, 'q', v3_results['session_id'])

    workspace_sessions_dom, _ = capture_page_state(
        urljoin(frontend_base, latest_session_href),
        expected_texts=['Workspace Run', '在 Workbench 复现'],
    )
    ensure(v3_results['workspace_id'] in workspace_sessions_dom, 'workspace sessions page should show workspace id')
    ensure(v3_results['subject_id'] in workspace_sessions_dom, 'workspace sessions page should show subject id')

    return {
        'workspace_url': workspace_url,
        'workspace_sessions_url': urljoin(frontend_base, latest_session_href),
    }


def run_v4_browser_smoke(ports: dict[str, int], v4_results: dict[str, str]) -> dict[str, str]:
    frontend_base = f"http://127.0.0.1:{ports['frontend']}"
    agent_session_params = {
        'run_kind': 'agent_run',
        'domain_workspace_id': v4_results['workspace_id'],
        'subject_id': v4_results['subject_id'],
        'agent_monitor_id': v4_results['monitor_id'],
        'trigger_kind': 'manual',
    }

    agent_sessions_url = (
        f"{frontend_base}/sessions?"
        f'{urlencode(agent_session_params)}'
    )
    agent_sessions_dom, _ = capture_page_state(
        agent_sessions_url,
        expected_texts=['Agent Run', '在 Workbench 复现'],
    )
    ensure(v4_results['monitor_id'] in agent_sessions_dom, 'agent sessions page should show monitor id')

    workbench_href = find_link_href(agent_sessions_dom, '在 Workbench 复现')
    ensure(workbench_href is not None, 'agent sessions page should expose workbench quick link')
    ensure_query_value(workbench_href, 'mode', 'debug')
    ensure_query_value(workbench_href, 'workspace_id', v4_results['workspace_id'])
    ensure_query_value(workbench_href, 'subject_id', v4_results['subject_id'])
    workbench_query = parse_qs(urlparse(workbench_href).query)
    ensure(workbench_query.get('preset', [''])[0], 'workbench link should preserve preset id')

    prompt_agent_dom, prompt_agent_text = capture_page_state(
        urljoin(frontend_base, workbench_href),
        expected_texts=['PROMPT WORKBENCH', 'PROMPT LIBRARY'],
    )
    ensure('PROMPT WORKBENCH' in prompt_agent_text, 'prompt-agent page should load the workbench shell')

    return {
        'agent_sessions_url': agent_sessions_url,
        'prompt_agent_url': urljoin(frontend_base, workbench_href),
    }


def run_browser_live_stack_smoke(ports: dict[str, int]) -> dict[str, str]:
    v3_results = run_v3_http_smoke(ports)
    v3_browser_results = run_v3_browser_smoke(ports, v3_results)
    v4_results = run_v4_http_smoke(ports['backend'])
    v4_browser_results = run_v4_browser_smoke(ports, v4_results)
    return {
        'workspace_url': v3_browser_results['workspace_url'],
        'workspace_sessions_url': v3_browser_results['workspace_sessions_url'],
        'agent_sessions_url': v4_browser_results['agent_sessions_url'],
        'prompt_agent_url': v4_browser_results['prompt_agent_url'],
    }


def main() -> None:
    ports, started_here = wait_for_browser_stack()
    try:
        results = run_browser_live_stack_smoke(ports)
        print('browser live-stack verification passed')
        print(f"frontend=http://127.0.0.1:{ports['frontend']}")
        print(f"backend=http://127.0.0.1:{ports['backend']}")
        print(f"workspace_url={results['workspace_url']}")
        print(f"workspace_sessions_url={results['workspace_sessions_url']}")
        print(f"agent_sessions_url={results['agent_sessions_url']}")
        print(f"prompt_agent_url={results['prompt_agent_url']}")
    finally:
        if started_here:
            subprocess.run([str(DEV_SCRIPT), 'stop'], cwd=ROOT_DIR, check=False)


if __name__ == '__main__':
    main()
