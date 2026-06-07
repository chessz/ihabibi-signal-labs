#!/usr/bin/env bash
# web-dev.sh — Frontend (apps/web) setup, refresh, dev server, and Docker DB helpers
#
# Usage:
#   ./scripts/web-dev.sh setup              First-time npm install + .env.local
#   ./scripts/web-dev.sh refresh            After git pull / dependency changes
#   ./scripts/web-dev.sh refresh --docker   Also restart Postgres container
#   ./scripts/web-dev.sh refresh --force    Reinstall deps + clear Vite cache
#   ./scripts/web-dev.sh dev                Start Vite dev server (port 5173)
#   ./scripts/web-dev.sh build              Production build
#   ./scripts/web-dev.sh check              Verify Node, deps, optional Docker
#   ./scripts/web-dev.sh docker up|down|restart|status
#
# Also:  signals-lab web <subcommand>  (thin wrapper)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB="${ROOT}/apps/web"
STAMP="${WEB}/.web-dev-stamp"
ENV_LOCAL="${WEB}/.env.local"
ENV_EXAMPLE="${WEB}/.env.example"
COMPOSE_FILE="${ROOT}/docker-compose.yml"
MIN_NODE_MAJOR=20
WEB_PORT="${WEB_PORT:-5173}"

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

_red()    { [[ -t 1 ]] && printf "\033[0;31m%s\033[0m\n" "$*" || printf "%s\n" "$*"; }
_green()  { [[ -t 1 ]] && printf "\033[0;32m%s\033[0m\n" "$*" || printf "%s\n" "$*"; }
_yellow() { [[ -t 1 ]] && printf "\033[0;33m%s\033[0m\n" "$*" || printf "%s\n" "$*"; }
_cyan()   { [[ -t 1 ]] && printf "\033[0;36m%s\033[0m\n" "$*" || printf "%s\n" "$*"; }
_bold()   { [[ -t 1 ]] && printf "\033[1;37m%s\033[0m\n" "$*" || printf "%s\n" "$*"; }

info()  { _cyan "→ $*"; }
ok()    { _green "✓ $*"; }
warn()  { _yellow "! $*"; }
die()   { _red "✗ $*" >&2; exit 1; }

usage() {
    cat <<EOF
Usage: ./scripts/web-dev.sh <command> [options]

Commands:
  setup                 npm install + create apps/web/.env.local
  refresh               Reconcile deps/env/cache after changes (run after git pull)
  dev                   Start Vite dev server on port ${WEB_PORT}
  build                 Production build to apps/web/dist
  check                 Verify Node, npm deps, Docker (optional)
  docker up|down|restart|status   TimescaleDB via docker compose

refresh options:
  --docker              Start/restart Postgres container if Docker available
  --force               npm install + clear Vite/dist cache even if unchanged
  --restart-dev         Kill dev server on port ${WEB_PORT} (if running)

Examples:
  ./scripts/web-dev.sh setup
  ./scripts/web-dev.sh refresh --docker
  ./scripts/web-dev.sh dev
  signals-lab web refresh
EOF
}

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------

require_web_dir() {
    [[ -d "$WEB" && -f "${WEB}/package.json" ]] || die "apps/web not found — run from repo root"
}

require_node() {
    command -v node >/dev/null 2>&1 || die "node not found — install Node.js ${MIN_NODE_MAJOR}+"
    command -v npm >/dev/null 2>&1 || die "npm not found"
    local major
    major="$(node -p 'process.versions.node.split(".")[0]')"
    if (( major < MIN_NODE_MAJOR )); then
        warn "Node ${MIN_NODE_MAJOR}+ recommended (found $(node -v))"
        warn "Vite 6 works on 20.15+; upgrade to 20.19+ when moving to Vite 8"
    else
        ok "Node $(node -v)"
    fi
}

docker_available() {
    command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

compose_cmd() {
    if docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
    else
        return 1
    fi
}

needs_npm_install() {
    local force="${1:-0}"
    [[ "$force" == "1" ]] && return 0
    [[ ! -d "${WEB}/node_modules" ]] && return 0
    [[ ! -f "${WEB}/package-lock.json" ]] && return 0

    # package.json or lockfile newer than last refresh or node_modules
    local marker="${WEB}/node_modules/.package-lock.json"
    [[ ! -f "$marker" ]] && return 0

    if [[ "${WEB}/package.json" -nt "$STAMP" ]] 2>/dev/null; then return 0; fi
    if [[ "${WEB}/package-lock.json" -nt "$STAMP" ]] 2>/dev/null; then return 0; fi
    return 1
}

env_needs_attention() {
    if [[ ! -f "$ENV_LOCAL" ]]; then
        return 0
    fi
    if [[ -f "$ENV_EXAMPLE" && "$ENV_EXAMPLE" -nt "$ENV_LOCAL" ]]; then
        return 0
    fi
    return 1
}

clear_vite_cache() {
    info "Clearing Vite cache and build output"
    rm -rf "${WEB}/node_modules/.vite" "${WEB}/dist"
    ok "Cache cleared"
}

setup_env_local() {
    if [[ ! -f "$ENV_LOCAL" && -f "$ENV_EXAMPLE" ]]; then
        cp "$ENV_EXAMPLE" "$ENV_LOCAL"
        ok "Created apps/web/.env.local from .env.example"
        return
    fi
    if env_needs_attention; then
        warn "apps/web/.env.example is newer than .env.local — review for new variables"
        _cyan "  diff: diff apps/web/.env.example apps/web/.env.local"
    fi
}

npm_install() {
    info "Installing npm dependencies (apps/web)"
    (cd "$WEB" && npm install)
    ok "npm dependencies installed"
}

touch_stamp() {
    mkdir -p "$WEB"
    date -u +"%Y-%m-%dT%H:%M:%SZ" >"$STAMP"
}

kill_dev_server() {
    if command -v lsof >/dev/null 2>&1; then
        local pids
        pids="$(lsof -ti :"${WEB_PORT}" 2>/dev/null || true)"
        if [[ -n "$pids" ]]; then
            info "Stopping process on port ${WEB_PORT}"
            # shellcheck disable=SC2086
            kill $pids 2>/dev/null || true
            sleep 1
            ok "Port ${WEB_PORT} freed — run: signals-lab web dev"
        fi
    fi
}

# ---------------------------------------------------------------------------
# Docker DB
# ---------------------------------------------------------------------------

cmd_docker() {
    local sub="${1:-status}"
    shift || true

    [[ -f "$COMPOSE_FILE" ]] || die "docker-compose.yml not found at repo root"

    if ! docker_available; then
        die "Docker is not running or not installed"
    fi

    local compose
    compose="$(compose_cmd)" || die "docker compose not available"

    case "$sub" in
        up|start)
            info "Starting TimescaleDB (signals-lab-db)"
            (cd "$ROOT" && $compose -f "$COMPOSE_FILE" up -d db)
            info "Waiting for Postgres..."
            local i
            for i in $(seq 1 30); do
                if (cd "$ROOT" && $compose -f "$COMPOSE_FILE" exec -T db pg_isready -U postgres >/dev/null 2>&1); then
                    ok "Postgres ready on localhost:5432 (signals_ts, signals_rel)"
                    _cyan "  URLs in .env: SIGNALSLAB_STORAGE__TIMESERIES__URL / RELATIONAL__URL"
                    return 0
                fi
                sleep 1
            done
            warn "Container started but health check timed out — run: signals-lab web docker status"
            ;;
        down|stop)
            info "Stopping TimescaleDB container"
            (cd "$ROOT" && $compose -f "$COMPOSE_FILE" down)
            ok "Docker stack stopped"
            ;;
        restart)
            cmd_docker down
            cmd_docker up
            ;;
        status|ps)
            (cd "$ROOT" && $compose -f "$COMPOSE_FILE" ps)
            ;;
        logs)
            (cd "$ROOT" && $compose -f "$COMPOSE_FILE" logs -f --tail=100 db)
            ;;
        *)
            die "Unknown docker subcommand: $sub (try: up, down, restart, status, logs)"
            ;;
    esac
}

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

cmd_setup() {
    local with_docker=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --docker) with_docker=1; shift ;;
            *) die "Unknown option: $1" ;;
        esac
    done

    _bold "Setting up signals-lab web (apps/web)..."
    require_web_dir
    require_node
    npm_install
    setup_env_local
    touch_stamp
    if [[ "$with_docker" == "1" ]]; then
        cmd_docker up
    elif ! docker_available; then
        warn "Docker not available — skip DB or install Docker for local Postgres"
    fi
    echo ""
    ok "Web setup complete"
    _cyan "  signals-lab web dev     → http://localhost:${WEB_PORT}"
    _cyan "  signals-lab web refresh → after git pull or package.json changes"
}

cmd_refresh() {
    local force=0
    local with_docker=0
    local restart_dev=0

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force) force=1; shift ;;
            --docker) with_docker=1; shift ;;
            --restart-dev) restart_dev=1; shift ;;
            *) die "Unknown option: $1" ;;
        esac
    done

    _bold "Refreshing web environment..."
    require_web_dir
    require_node

    local changed=0

    if needs_npm_install "$force"; then
        npm_install
        changed=1
    else
        ok "npm dependencies up to date"
    fi

    if [[ "$force" == "1" ]]; then
        clear_vite_cache
        changed=1
    elif needs_npm_install 0; then
        : # already installed above
    elif [[ ! -d "${WEB}/node_modules/.vite" ]]; then
        ok "Vite cache OK"
    fi

    setup_env_local

    if [[ "$with_docker" == "1" ]]; then
        if docker_available; then
            cmd_docker restart
            changed=1
        else
            warn "--docker requested but Docker is not available"
        fi
    fi

    if [[ "$restart_dev" == "1" ]]; then
        kill_dev_server
        changed=1
    fi

    touch_stamp

    echo ""
    if [[ "$changed" == "1" ]]; then
        ok "Refresh applied — restart dev server if it was running"
        _cyan "  signals-lab web dev"
    else
        ok "Nothing required a refresh (use --force to reinstall anyway)"
    fi

    if env_needs_attention; then
        warn "Update apps/web/.env.local if .env.example added new keys"
    fi
}

cmd_dev() {
    require_web_dir
    require_node
    [[ -d "${WEB}/node_modules" ]] || {
        warn "node_modules missing — running setup first"
        cmd_setup
    }
    info "Starting Vite dev server → http://localhost:${WEB_PORT}"
    _dim "Press Ctrl+C to stop. After git pull run: signals-lab web refresh"
    (cd "$WEB" && npm run dev -- --host 127.0.0.1 --port "$WEB_PORT")
}

cmd_build() {
    require_web_dir
    require_node
    [[ -d "${WEB}/node_modules" ]] || cmd_setup
    info "Building production bundle"
    (cd "$WEB" && npm run build)
    ok "Built → apps/web/dist"
}

cmd_check() {
    _bold "Checking web environment..."
    require_web_dir
    require_node

    if [[ -d "${WEB}/node_modules" ]]; then
        ok "node_modules present"
    else
        warn "node_modules missing — run: signals-lab web setup"
    fi

    if [[ -f "$ENV_LOCAL" ]]; then
        ok "apps/web/.env.local exists"
    else
        warn "apps/web/.env.local missing — run: signals-lab web setup"
    fi

    if docker_available; then
        ok "Docker available"
        if compose_cmd >/dev/null 2>&1; then
            (cd "$ROOT" && $(compose_cmd) -f "$COMPOSE_FILE" ps 2>/dev/null) || true
        fi
    else
        warn "Docker not running (optional — for local Postgres)"
    fi

    if [[ -f "$STAMP" ]]; then
        _cyan "  Last refresh: $(cat "$STAMP")"
    fi
    echo ""
    ok "Web check complete"
}

_dim() { _cyan "$@"; }

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
    local cmd="${1:-help}"
    shift || true

    case "$cmd" in
        setup)    cmd_setup "$@" ;;
        refresh)  cmd_refresh "$@" ;;
        dev|serve|start) cmd_dev "$@" ;;
        build)    cmd_build "$@" ;;
        check)    cmd_check "$@" ;;
        docker)   cmd_docker "$@" ;;
        help|-h|--help) usage ;;
        *)
            die "Unknown command: $cmd (try: setup, refresh, dev, build, check, docker)"
            ;;
    esac
}

main "$@"
