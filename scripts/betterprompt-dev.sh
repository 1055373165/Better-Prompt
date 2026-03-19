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
BACKEND_PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
BACKEND_ALEMBIC_BIN="$BACKEND_DIR/.venv/bin/alembic"
BACKEND_ALEMBIC_CONFIG="$BACKEND_DIR/alembic.ini"
BACKEND_UVICORN_BIN="$BACKEND_DIR/.venv/bin/uvicorn"

BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

DEFAULT_BACKEND_PORT="${BETTERPROMPT_DEV_BACKEND_PORT:-8000}"
DEFAULT_FRONTEND_PORT="${BETTERPROMPT_DEV_FRONTEND_PORT:-5173}"
MIN_BACKEND_PYTHON_MINOR=11
MIN_NODE_MAJOR=18

BACKEND_PORT="$DEFAULT_BACKEND_PORT"
FRONTEND_PORT="$DEFAULT_FRONTEND_PORT"
BACKEND_HEALTH_URL=""
FRONTEND_URL=""
NODE_BIN=""

mkdir -p "$LOG_DIR"


print_help() {
  cat <<'EOF'
Usage: ./scripts/betterprompt-dev.sh <command>

Commands:
  start    Start backend and frontend in the background
  stop     Stop backend and frontend
  restart  Restart backend and frontend
  status   Show current process status
  ports    Show port diagnostics and conflict details
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


print_port_conflict_details() {
  local port="$1"
  local prefix="${2:-}"
  local had_details=0

  while read -r pid command endpoint; do
    [[ -z "$pid" ]] && continue
    had_details=1

    local args
    args="$(ps -p "$pid" -o args= 2>/dev/null | sed 's/^[[:space:]]*//' || true)"
    if [[ -n "$args" ]]; then
      echo "${prefix}port $port -> pid $pid (${command}) ${endpoint} :: $args"
    else
      echo "${prefix}port $port -> pid $pid (${command}) ${endpoint}"
    fi
  done < <(lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | awk 'NR>1 {print $2, $1, $9}')

  if [[ "$had_details" -eq 0 ]]; then
    echo "${prefix}port $port is occupied."
  fi
}


extract_major_version() {
  local version="$1"
  version="${version#v}"
  echo "${version%%.*}"
}


backend_python_version() {
  "$BACKEND_PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null
}


backend_python_is_compatible() {
  "$BACKEND_PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1
}


node_version() {
  local node_bin="$1"
  "$node_bin" --version 2>/dev/null
}


is_node_compatible() {
  local node_bin="$1"
  local version
  local major

  version="$(node_version "$node_bin")" || return 1
  major="$(extract_major_version "$version")"

  [[ "$major" =~ ^[0-9]+$ ]] || return 1
  ((major >= MIN_NODE_MAJOR))
}


resolve_node_bin() {
  local candidate

  if [[ -n "${BETTERPROMPT_DEV_NODE_BIN:-}" ]]; then
    candidate="$BETTERPROMPT_DEV_NODE_BIN"
    if [[ ! -x "$candidate" ]]; then
      echo "BETTERPROMPT_DEV_NODE_BIN is not executable: $candidate"
      exit 1
    fi
    if ! is_node_compatible "$candidate"; then
      echo "BETTERPROMPT_DEV_NODE_BIN must point to Node.js ${MIN_NODE_MAJOR}+ but found $(node_version "$candidate")."
      exit 1
    fi
    NODE_BIN="$candidate"
    return 0
  fi

  if command -v node >/dev/null 2>&1; then
    candidate="$(command -v node)"
    if is_node_compatible "$candidate"; then
      NODE_BIN="$candidate"
      return 0
    fi
  fi

  for candidate in \
    /opt/homebrew/bin/node \
    /usr/local/bin/node \
    /opt/homebrew/opt/node/bin/node \
    /usr/local/opt/node/bin/node
  do
    if [[ -x "$candidate" ]] && is_node_compatible "$candidate"; then
      NODE_BIN="$candidate"
      return 0
    fi
  done

  return 1
}


find_available_port() {
  local label="$1"
  local preferred_port="$2"
  local candidate="$preferred_port"
  local -a occupied_ports=()

  for ((i=0; i<50; i++)); do
    if ! port_in_use "$candidate"; then
      if [[ "${#occupied_ports[@]}" -gt 0 ]]; then
        echo "$label preferred port $preferred_port is already occupied." >&2
        for occupied_port in "${occupied_ports[@]}"; do
          print_port_conflict_details "$occupied_port" "  - " >&2
        done
        echo "$label will use port $candidate instead." >&2
      fi
      echo "$candidate"
      return 0
    fi
    occupied_ports+=("$candidate")
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
  if [[ ! -x "$BACKEND_PYTHON_BIN" ]]; then
    echo "Missing backend virtualenv. Expected: $BACKEND_PYTHON_BIN"
    echo "Create it with:"
    echo "  cd $BACKEND_DIR"
    echo "  uv venv --python python3.11 .venv"
    echo "  uv pip install --python .venv/bin/python -e ."
    exit 1
  fi

  local backend_python
  backend_python="$(backend_python_version)"
  if [[ -z "$backend_python" ]] || ! backend_python_is_compatible; then
    echo "Backend virtualenv must use Python 3.${MIN_BACKEND_PYTHON_MINOR}+ but found ${backend_python:-unknown}."
    echo "Recreate it with:"
    echo "  cd $BACKEND_DIR"
    echo "  uv venv --clear --python python3.11 .venv"
    echo "  uv pip install --python .venv/bin/python -e ."
    exit 1
  fi

  if [[ ! -x "$BACKEND_UVICORN_BIN" ]]; then
    echo "Backend dependencies are missing. Expected: $BACKEND_UVICORN_BIN"
    echo "Install them with:"
    echo "  cd $BACKEND_DIR"
    echo "  uv pip install --python .venv/bin/python -e ."
    exit 1
  fi

  if [[ ! -f "$BACKEND_DIR/.env" ]]; then
    echo "Missing backend env file. Create it first: $BACKEND_DIR/.env"
    exit 1
  fi

  if [[ ! -x "$BACKEND_ALEMBIC_BIN" ]]; then
    echo "Missing Alembic binary. Expected: $BACKEND_ALEMBIC_BIN"
    echo "Install backend dependencies with:"
    echo "  cd $BACKEND_DIR"
    echo "  uv pip install --python .venv/bin/python -e ."
    exit 1
  fi

  if [[ ! -f "$BACKEND_ALEMBIC_CONFIG" ]]; then
    echo "Missing Alembic config. Expected: $BACKEND_ALEMBIC_CONFIG"
    exit 1
  fi
}


ensure_frontend_ready() {
  if [[ ! -x "$FRONTEND_BIN" ]]; then
    echo "Frontend dependencies are missing. Run: cd $FRONTEND_DIR && npm install"
    exit 1
  fi

  if ! resolve_node_bin; then
    local current_version="missing"
    if command -v node >/dev/null 2>&1; then
      current_version="$(node --version 2>/dev/null || echo unknown)"
    fi
    echo "A Node.js ${MIN_NODE_MAJOR}+ runtime is required to start the frontend."
    echo "Current shell node: $current_version"
    echo "Install a newer Node.js, or set BETTERPROMPT_DEV_NODE_BIN=/path/to/node"
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

  echo "Running backend migrations..."
  (
    cd "$BACKEND_DIR"
    "$BACKEND_ALEMBIC_BIN" -c "$BACKEND_ALEMBIC_CONFIG" upgrade head
  )

  spawn_service \
    "$BACKEND_DIR" \
    "$BACKEND_PID_FILE" \
    "$BACKEND_LOG" \
    "$BACKEND_UVICORN_BIN" \
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

  if [[ "$(command -v node 2>/dev/null || true)" != "$NODE_BIN" ]]; then
    echo "Using Node runtime for frontend: $(node_version "$NODE_BIN") ($NODE_BIN)"
  fi

  spawn_service \
    "$FRONTEND_DIR" \
    "$FRONTEND_PID_FILE" \
    "$FRONTEND_LOG" \
    PATH="$(dirname "$NODE_BIN"):$PATH" \
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


show_port_diagnostics() {
  load_runtime_config
  sync_ports_with_running_processes

  echo "Port diagnostics:"

  if port_in_use "$BACKEND_PORT"; then
    echo "Backend target port: $BACKEND_PORT (occupied)"
    print_port_conflict_details "$BACKEND_PORT" "  - "
  else
    echo "Backend target port: $BACKEND_PORT (available)"
  fi

  if port_in_use "$FRONTEND_PORT"; then
    echo "Frontend target port: $FRONTEND_PORT (occupied)"
    print_port_conflict_details "$FRONTEND_PORT" "  - "
  else
    echo "Frontend target port: $FRONTEND_PORT (available)"
  fi
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
  ports)
    show_port_diagnostics
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
