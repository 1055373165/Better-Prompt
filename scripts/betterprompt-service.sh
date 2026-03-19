#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_SCRIPT="$ROOT_DIR/scripts/betterprompt-dev.sh"

print_help() {
  cat <<'EOF'
Usage: ./scripts/betterprompt-service.sh <command>

Commands:
  up, start       Start backend and frontend
  down, stop      Stop backend and frontend
  restart         Restart backend and frontend
  status          Show current process status
  ports           Show port diagnostics and conflict details
  logs            Tail backend and frontend logs
  help            Show this help message
EOF
}

if [[ ! -x "$TARGET_SCRIPT" ]]; then
  echo "Missing target script: $TARGET_SCRIPT"
  exit 1
fi

command="${1:-help}"

case "$command" in
  up|start)
    exec "$TARGET_SCRIPT" start
    ;;
  down|stop)
    exec "$TARGET_SCRIPT" stop
    ;;
  restart)
    exec "$TARGET_SCRIPT" restart
    ;;
  status)
    exec "$TARGET_SCRIPT" status
    ;;
  ports)
    exec "$TARGET_SCRIPT" ports
    ;;
  logs)
    exec "$TARGET_SCRIPT" logs
    ;;
  help|--help|-h)
    print_help
    ;;
  *)
    echo "Unknown command: $command"
    echo
    print_help
    exit 1
    ;;
esac
