#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT_DIR/betterprompt"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
RUN_DIR="$APP_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
FRONTEND_BIN="$FRONTEND_DIR/node_modules/.bin/vite"
PORTS_FILE="$RUN_DIR/dev-ports.env"

BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

DEFAULT_BACKEND_PORT="${BETTERPROMPT_DEV_BACKEND_PORT:-8000}"
DEFAULT_FRONTEND_PORT="${BETTERPROMPT_DEV_FRONTEND_PORT:-5173}"

BACKEND_PORT="$DEFAULT_BACKEND_PORT"
FRONTEND_PORT="$DEFAULT_FRONTEND_PORT"
BACKEND_HEALTH_URL=""
FRONTEND_URL=""

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


refresh_urls() {
  BACKEND_HEALTH_URL="http://127.0.0.1:${BACKEND_PORT}/api/v1/health"
  FRONTEND_URL="http://127.0.0.1:${FRONTEND_PORT}"
}


load_runtime_config() {
  BACKEND_PORT="$DEFAULT_BACKEND_PORT"
  FRONTEND_PORT="$DEFAULT_FRONTEND_PORT"

  if [[ -f "$PORTS_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$PORTS_FILE"
  fi

  BACKEND_PORT="${BACKEND_PORT:-$DEFAULT_BACKEND_PORT}"
  FRONTEND_PORT="${FRONTEND_PORT:-$DEFAULT_FRONTEND_PORT}"
  refresh_urls
}


save_runtime_config() {
  cat >"$PORTS_FILE" <<EOF
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
EOF
}


clear_runtime_config() {
  rm -f "$PORTS_FILE"
  BACKEND_PORT="$DEFAULT_BACKEND_PORT"
  FRONTEND_PORT="$DEFAULT_FRONTEND_PORT"
  refresh_urls
}


port_in_use() {
  local port="$1"
  lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}


find_available_port() {
  local label="$1"
  local preferred_port="$2"
  local candidate="$preferred_port"

  for ((i=0; i<50; i++)); do
    if ! port_in_use "$candidate"; then
      if [[ "$candidate" != "$preferred_port" ]]; then
        echo "$label port $preferred_port is in use, using $candidate instead." >&2
      fi
      echo "$candidate"
      return 0
    fi
    candidate=$((candidate + 1))
  done

  echo "Unable to find an available port for $label after checking 50 candidates." >&2
  exit 1
}


detect_port_by_pid() {
  local pid="$1"
  lsof -nP -a -p "$pid" -iTCP -sTCP:LISTEN 2>/dev/null | awk 'NR==2 {split($9, parts, ":"); print parts[length(parts)]}'
}


sync_ports_with_running_processes() {
  if is_running "$BACKEND_PID_FILE"; then
    local backend_pid
    backend_pid="$(cat "$BACKEND_PID_FILE")"
    local detected_backend_port
    detected_backend_port="$(detect_port_by_pid "$backend_pid")"
    if [[ -n "$detected_backend_port" ]]; then
      BACKEND_PORT="$detected_backend_port"
    fi
  fi

  if is_running "$FRONTEND_PID_FILE"; then
    local frontend_pid
    frontend_pid="$(cat "$FRONTEND_PID_FILE")"
    local detected_frontend_port
    detected_frontend_port="$(detect_port_by_pid "$frontend_pid")"
    if [[ -n "$detected_frontend_port" ]]; then
      FRONTEND_PORT="$detected_frontend_port"
    fi
  fi

  refresh_urls
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
    nohup env "$@" </dev/null >"$log_file" 2>&1 &
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
  load_runtime_config
  sync_ports_with_running_processes

  if is_running "$BACKEND_PID_FILE"; then
    save_runtime_config
    echo "Backend already running (pid $(cat "$BACKEND_PID_FILE"), port $BACKEND_PORT)."
    return 0
  fi

  BACKEND_PORT="$(find_available_port "Backend" "$DEFAULT_BACKEND_PORT")"
  refresh_urls
  save_runtime_config

  spawn_service \
    "$BACKEND_DIR" \
    "$BACKEND_PID_FILE" \
    "$BACKEND_LOG" \
    .venv/bin/uvicorn \
    app.main:app \
    --host 127.0.0.1 \
    --port "$BACKEND_PORT"

  wait_for_url "Backend" "$BACKEND_HEALTH_URL" "$BACKEND_LOG"
}


start_frontend() {
  ensure_frontend_ready
  load_runtime_config
  sync_ports_with_running_processes

  if is_running "$FRONTEND_PID_FILE"; then
    save_runtime_config
    echo "Frontend already running (pid $(cat "$FRONTEND_PID_FILE"), port $FRONTEND_PORT)."
    return 0
  fi

  FRONTEND_PORT="$(find_available_port "Frontend" "$DEFAULT_FRONTEND_PORT")"
  refresh_urls
  save_runtime_config

  spawn_service \
    "$FRONTEND_DIR" \
    "$FRONTEND_PID_FILE" \
    "$FRONTEND_LOG" \
    BETTERPROMPT_BACKEND_PORT="$BACKEND_PORT" \
    BETTERPROMPT_FRONTEND_PORT="$FRONTEND_PORT" \
    "$FRONTEND_BIN" \
    --host 127.0.0.1 \
    --port "$FRONTEND_PORT"

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
  load_runtime_config
  sync_ports_with_running_processes

  if is_running "$BACKEND_PID_FILE"; then
    echo "Backend: running (pid $(cat "$BACKEND_PID_FILE"), port $BACKEND_PORT)"
  else
    echo "Backend: stopped"
  fi

  if is_running "$FRONTEND_PID_FILE"; then
    echo "Frontend: running (pid $(cat "$FRONTEND_PID_FILE"), port $FRONTEND_PORT)"
  else
    echo "Frontend: stopped"
  fi

  echo "Backend health: $BACKEND_HEALTH_URL"
  echo "Frontend URL:   $FRONTEND_URL"
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
    clear_runtime_config
    ;;
  restart)
    stop_service "Frontend" "$FRONTEND_PID_FILE"
    stop_service "Backend" "$BACKEND_PID_FILE"
    clear_runtime_config
    start_backend
    start_frontend
    echo
    echo "BetterPrompt is up:"
    echo "- Frontend: $FRONTEND_URL"
    echo "- Backend:  $BACKEND_HEALTH_URL"
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
