#!/usr/bin/env bash
# setup.sh — Bootstrap signals-lab development environment
#
# Usage:
#   ./setup.sh              Full install (venv + deps + .env)
#   ./setup.sh --check      Verify environment only (no install)
#   ./setup.sh --dev-only   Skip optional ta-lib install
#
# After setup:
#   export PATH="$(pwd)/bin:$PATH"   # optional: run `signals-lab` from anywhere
#   signals-lab config validate
#   signals-lab check

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${ROOT}/.venv"
PYTHON="${VENV}/bin/python"
PIP="${VENV}/bin/pip"
MIN_PYTHON="3.11"

# ---------------------------------------------------------------------------
# Output helpers
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

# Core runtime deps (ta-lib excluded — often needs system libta-lib)
CORE_DEPS=(
    "pydantic>=2.7.0"
    "pydantic-settings>=2.3.0"
    "pyyaml>=6.0.1"
    "python-dotenv>=1.0.1"
    "aiohttp>=3.9.0"
    "httpx>=0.27.0"
    "websockets>=12.0"
    "asyncpg>=0.29.0"
    "sqlalchemy>=2.0.30"
    "alembic>=1.13.0"
    "psycopg2-binary>=2.9.9"
    "fastapi>=0.110.0"
    "uvicorn[standard]>=0.29.0"
    "python-multipart>=0.0.9"
    "apscheduler>=3.10.4"
    "tenacity>=8.2.3"
    "numpy>=1.26.0"
    "pandas>=2.2.0"
    "structlog>=24.1.0"
    "loguru>=0.7.2"
    "python-json-logger>=2.0.7"
    "rich>=13.7.0"
    "typer>=0.12.0"
    "prometheus-client>=0.19.0"
    "orjson>=3.10.0"
    "msgpack>=1.0.8"
)

DEV_DEPS=(
    "pytest>=8.2.0"
    "pytest-asyncio>=0.23.0"
    "pytest-cov>=5.0.0"
    "pytest-mock>=3.14.0"
    "ruff>=0.4.0"
    "mypy>=1.10.0"
    "fpdf2>=2.7.0"
)

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

check_python() {
    if ! command -v python3 &>/dev/null; then
        die "python3 not found. Install Python ${MIN_PYTHON}+ first."
    fi
    local ver
    ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" \
        || die "Python ${MIN_PYTHON}+ required (found ${ver})"
    ok "Python ${ver}"
}

check_venv() {
    [[ -x "$PYTHON" ]] || die "Virtual environment missing. Run ./setup.sh without --check"
}

check_import() {
    local module="$1"
    "$PYTHON" -c "import ${module}" 2>/dev/null
}

check_deps() {
    local missing=()
    for mod in asyncpg httpx pydantic yaml structlog; do
        if ! check_import "$mod"; then
            missing+=("$mod")
        fi
    done
    if ((${#missing[@]} > 0)); then
        die "Missing Python modules: ${missing[*]}. Run ./setup.sh"
    fi
    ok "Core Python dependencies"
}

check_env_file() {
    if [[ -f "${ROOT}/.env" ]]; then
        ok ".env exists"
    else
        warn ".env missing — copy .env.example and add API keys"
    fi
}

check_postgres_hint() {
    if command -v psql &>/dev/null; then
        ok "psql found (PostgreSQL client)"
    else
        warn "psql not found — ingestion/API need PostgreSQL + TimescaleDB"
    fi
    if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
        ok "Docker available — run: signals-lab web docker up"
    else
        _cyan "  Docker: signals-lab web docker up"
        _cyan "  Or: docker compose up -d db  (see docker-compose.yml)"
    fi
}

cmd_check() {
    _bold "Checking signals-lab environment..."
    check_python
    check_venv
    check_deps
    check_env_file
    check_postgres_hint
    echo ""
    ok "Environment looks good"
}

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------

create_venv() {
    if [[ -d "$VENV" ]]; then
        warn ".venv already exists — reusing"
    else
        info "Creating virtual environment at .venv"
        python3 -m venv "$VENV"
    fi
    ok "Virtual environment ready"
}

install_package() {
    info "Upgrading pip"
    "$PIP" install -q --upgrade pip setuptools wheel

    info "Installing signals-lab (editable, no deps yet)"
    "$PIP" install -q -e . --no-deps

    info "Installing core dependencies"
    "$PIP" install -q "${CORE_DEPS[@]}"

    info "Installing dev dependencies"
    "$PIP" install -q "${DEV_DEPS[@]}"

    if [[ "${SKIP_TALIB:-0}" != "1" ]]; then
        info "Attempting optional ta-lib install (may fail without system libta-lib)"
        if "$PIP" install -q "ta-lib>=0.4.28" 2>/dev/null; then
            ok "ta-lib installed"
        else
            warn "ta-lib skipped — features use pure-Python math for now"
            warn "To install later: sudo apt install libta-lib-dev && pip install ta-lib"
        fi
    else
        warn "Skipping ta-lib (--dev-only)"
    fi

    ok "Dependencies installed"
}

setup_env_file() {
    if [[ ! -f "${ROOT}/.env" && -f "${ROOT}/.env.example" ]]; then
        cp "${ROOT}/.env.example" "${ROOT}/.env"
        ok "Created .env from .env.example — edit with your API keys"
    fi
}

validate_config() {
    info "Validating configuration"
    cd "$ROOT"
    export PYTHONPATH="${ROOT}/src"
    if "$PYTHON" -c "from signals_lab.config import get_settings; get_settings(reload=True)"; then
        ok "config/settings.yaml loads cleanly"
    else
        die "Configuration validation failed"
    fi
}

print_next_steps() {
    echo ""
    _bold "Setup complete!"
    echo ""
    _cyan "Activate the venv (optional):"
    echo "  source .venv/bin/activate"
    echo ""
    _cyan "Or add bin/ to your PATH:"
    echo "  export PATH=\"${ROOT}/bin:\$PATH\""
    echo ""
    _cyan "Then try:"
    echo "  signals-lab help"
    echo "  signals-lab config show"
    echo "  signals-lab features compute    # no database needed"
    echo "  signals-lab check               # run tests"
    echo ""
    _cyan "For ingestion (needs PostgreSQL/TimescaleDB):"
    echo "  signals-lab web docker up       # or: docker compose up -d db"
    echo "  signals-lab ingest status"
    echo "  signals-lab ingest once"
    echo "  signals-lab run                 # alias for ingest start"
    echo ""
    _cyan "For the web dashboard (apps/web):"
    echo "  signals-lab web setup           # first time"
    echo "  signals-lab web refresh         # after git pull / dep changes"
    echo "  signals-lab web dev             # http://localhost:5173"
    echo ""
    warn "Ingestion requires databases at the URLs in .env / config/settings.yaml"
}

cmd_install() {
    _bold "Setting up signals-lab..."
    cd "$ROOT"
    check_python
    create_venv
    install_package
    setup_env_file
    validate_config
    print_next_steps
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

usage() {
    cat <<EOF
Usage: ./setup.sh [OPTIONS]

Bootstrap the signals-lab Python environment (.venv + dependencies).

Options:
  --check       Verify environment only (no install)
  --dev-only    Skip optional ta-lib install
  -h, --help    Show this help

Examples:
  ./setup.sh
  ./setup.sh --check
  export PATH="\$(pwd)/bin:\$PATH" && signals-lab run
EOF
}

main() {
    local mode="install"
    SKIP_TALIB=0

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --check)   mode="check"; shift ;;
            --dev-only) SKIP_TALIB=1; shift ;;
            -h|--help) usage; exit 0 ;;
            *) die "Unknown option: $1 (try --help)" ;;
        esac
    done

    case "$mode" in
        check)   cmd_check ;;
        install) cmd_install ;;
    esac
}

main "$@"
