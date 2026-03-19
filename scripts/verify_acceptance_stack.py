#!/usr/bin/env python3
from __future__ import annotations

import subprocess

from verify_browser_live_stack import browser_binary, run_browser_live_stack_smoke, wait_for_browser_stack
from verify_v2_stack import DEV_SCRIPT, ROOT_DIR, run_http_smoke as run_v2_http_smoke


def main() -> None:
    browser_binary()
    ports, started_here = wait_for_browser_stack()
    try:
        v2_results = run_v2_http_smoke(ports)
        browser_results = run_browser_live_stack_smoke(ports)
        print('acceptance stack verification passed')
        print(f"frontend=http://127.0.0.1:{ports['frontend']}")
        print(f"backend=http://127.0.0.1:{ports['backend']}")
        print(f"v2_run_preset_id={v2_results['run_preset_id']}")
        print(f"v2_session_id={v2_results['session_id']}")
        print(f"v2_iteration_id={v2_results['iteration_id']}")
        print(f"workspace_url={browser_results['workspace_url']}")
        print(f"workspace_sessions_url={browser_results['workspace_sessions_url']}")
        print(f"agent_sessions_url={browser_results['agent_sessions_url']}")
        print(f"prompt_agent_url={browser_results['prompt_agent_url']}")
    finally:
        if started_here:
            subprocess.run([str(DEV_SCRIPT), 'stop'], cwd=ROOT_DIR, check=False)


if __name__ == '__main__':
    main()
