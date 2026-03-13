#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT_DIR/betterprompt"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
RUN_DIR="$APP_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
FRONTEND_BIN="$FRONTEND_DIR/node_modules/.bin/vite"

BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

BACKEND_HEALTH_URL="http://127.0.0.1:8000/api/v1/health"
FRONTEND_URL="http://127.0.0.1:5173"

mkdir -p "$LOG_DIR"


print_help() {
  cat <<'EOF'
Usage: ./scripts/betterprompt-dev.sh <command>

Commands:
  start    Start backend and frontend in the background
  stop     Stop backend and frontend
  restart  Restart backend and frontend
  status   Show current process status
  logs     Tail backend and frontend logs
EOF
}


is_running() {
  local pid_file="$1"

  if [[ ! -f "$pid_file" ]]; then
    return 1
  fi

  local pid
  pid="$(cat "$pid_file")"

  if kill -0 "$pid" >/dev/null 2>&1; then
    return 0
  fi

  rm -f "$pid_file"
  return 1
}


wait_for_url() {
  local name="$1"
  local url="$2"
  local log_file="$3"

  for ((i=1; i<=40; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "$name is ready: $url"
      return 0
    fi
    sleep 1
  done

  echo "Failed to start $name. Recent logs:"
  tail -n 40 "$log_file" || true
  exit 1
}


spawn_service() {
  local workdir="$1"
  local pid_file="$2"
  local log_file="$3"
  shift 3

  (
    cd "$workdir"
    nohup "$@" </dev/null >"$log_file" 2>&1 &
    echo $! >"$pid_file"
  )
}


ensure_backend_ready() {
  if [[ ! -x "$BACKEND_DIR/.venv/bin/uvicorn" ]]; then
    echo "Missing backend virtualenv. Expected: $BACKEND_DIR/.venv/bin/uvicorn"
    exit 1
  fi

  if [[ ! -f "$BACKEND_DIR/.env" ]]; then
    echo "Missing backend env file. Create it first: $BACKEND_DIR/.env"
    exit 1
  fi
}


ensure_frontend_ready() {
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm is required but was not found in PATH."
    exit 1
  fi

  if [[ ! -x "$FRONTEND_BIN" ]]; then
    echo "Frontend dependencies are missing. Run: cd $FRONTEND_DIR && npm install"
    exit 1
  fi
}


start_backend() {
  ensure_backend_ready

  if is_running "$BACKEND_PID_FILE"; then
    echo "Backend already running (pid $(cat "$BACKEND_PID_FILE"))."
    return 0
  fi

  spawn_service \
    "$BACKEND_DIR" \
    "$BACKEND_PID_FILE" \
    "$BACKEND_LOG" \
    .venv/bin/uvicorn \
    app.main:app \
    --host 127.0.0.1 \
    --port 8000

  wait_for_url "Backend" "$BACKEND_HEALTH_URL" "$BACKEND_LOG"
}


start_frontend() {
  ensure_frontend_ready

  if is_running "$FRONTEND_PID_FILE"; then
    echo "Frontend already running (pid $(cat "$FRONTEND_PID_FILE"))."
    return 0
  fi

  spawn_service \
    "$FRONTEND_DIR" \
    "$FRONTEND_PID_FILE" \
    "$FRONTEND_LOG" \
    "$FRONTEND_BIN" \
    --host 127.0.0.1 \
    --port 5173

  wait_for_url "Frontend" "$FRONTEND_URL" "$FRONTEND_LOG"
}


stop_service() {
  local name="$1"
  local pid_file="$2"

  if ! is_running "$pid_file"; then
    echo "$name is not running."
    return 0
  fi

  local pid
  pid="$(cat "$pid_file")"
  kill "$pid" >/dev/null 2>&1 || true

  for ((i=1; i<=10; i++)); do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      rm -f "$pid_file"
      echo "$name stopped."
      return 0
    fi
    sleep 1
  done

  kill -9 "$pid" >/dev/null 2>&1 || true
  rm -f "$pid_file"
  echo "$name force-stopped."
}


show_status() {
  if is_running "$BACKEND_PID_FILE"; then
    echo "Backend: running (pid $(cat "$BACKEND_PID_FILE"))"
  else
    echo "Backend: stopped"
  fi

  if is_running "$FRONTEND_PID_FILE"; then
    echo "Frontend: running (pid $(cat "$FRONTEND_PID_FILE"))"
  else
    echo "Frontend: stopped"
  fi

  echo "Backend log:  $BACKEND_LOG"
  echo "Frontend log: $FRONTEND_LOG"
}


tail_logs() {
  touch "$BACKEND_LOG" "$FRONTEND_LOG"
  tail -n 60 -f "$BACKEND_LOG" "$FRONTEND_LOG"
}


command="${1:-help}"

case "$command" in
  start)
    start_backend
    start_frontend
    echo
    echo "BetterPrompt is up:"
    echo "- Frontend: $FRONTEND_URL"
    echo "- Backend:  $BACKEND_HEALTH_URL"
    ;;
  stop)
    stop_service "Frontend" "$FRONTEND_PID_FILE"
    stop_service "Backend" "$BACKEND_PID_FILE"
    ;;
  restart)
    stop_service "Frontend" "$FRONTEND_PID_FILE"
    stop_service "Backend" "$BACKEND_PID_FILE"
    start_backend
    start_frontend
    ;;
  status)
    show_status
    ;;
  logs)
    tail_logs
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
