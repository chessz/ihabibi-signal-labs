# signals-lab

High-performance crypto market signal research platform.

**signals-lab** is a research-grade platform that:
- Ingests market, social, sentiment, on-chain, and event/geopolitical data
- Computes reusable research features
- Generates ranked buy/sell/watch signals with explainable confidence scores
- Tracks paper outcomes and P/L over time
- Exposes approved signals and performance metrics through an API for [iHabibi Trading](https://ihabibi.com)

> **⚠️ This is NOT a live trading system.** It performs research, paper evaluation, and signal publishing only. No exchange orders are placed.

## Architecture

```
Ingestion Workers → Time-Series Storage → Feature Engine → Signal Engine → (Paper Evaluator + Publisher API)
```

- **Ingestion**: Market (Binance), Social (LunarCrush), On-Chain (Glassnode), Events (NewsAPI)
- **Features**: Trend, momentum, mean reversion, volatility, social, on-chain, events, cross-asset
- **Signals**: Confidence-calibrated (low/medium/high/extreme), only high/extreme published
- **Evaluation**: Full paper trading with win rate, expectancy, profit factor, decay analysis
- **API**: FastAPI with signal publishing, performance metrics, health checks

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design document.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL with TimescaleDB extension (for time-series data)
- API keys for data providers (optional - mock providers included)

### Setup

```bash
# Clone the repository
git clone git@github.com:chessz/ihabibi-signal-labs.git
cd ihabibi-signal-labs

# Create virtual environment and install
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Run database migrations (requires PostgreSQL + TimescaleDB)
# python scripts/migrate.py

# Start ingestion scheduler
python -m signals_lab.cli.main ingest

# Generate signals
python -m signals_lab.cli.main signals generate

# Start API server
python -m signals_lab.cli.main api serve
```

## Project Structure

```
signals-lab/
├── config/                  # YAML configuration files
├── src/signals_lab/         # Main Python package
│   ├── domain/              # Domain models (Pydantic)
│   ├── storage/             # Database abstractions
│   ├── ingestion/           # Data ingestion services
│   ├── features/            # Feature engineering
│   ├── signals/             # Signal generation
│   ├── evaluation/          # Paper trading evaluation
│   ├── api/                 # FastAPI application
│   ├── workers/             # Background workers
│   └── utils/               # Shared utilities
├── tests/                   # Test suite
├── ARCHITECTURE.md          # Detailed architecture document
└── pyproject.toml           # Project configuration
```

## API Endpoints

```
GET  /api/v1/signals              # Latest published signals (high/extreme only)
GET  /api/v1/signals/{signal_id}  # Signal details with justification
GET  /api/v1/signals/history      # Historical signals with filters
GET  /api/v1/performance/summary  # Overall performance metrics
GET  /api/v1/performance/confidence-bands  # Stats by confidence band
GET  /api/v1/performance/regimes  # Stats by market regime
GET  /api/v1/performance/strategies  # Stats by signal family
GET  /api/v1/health               # Health check
GET  /api/v1/providers/status     # Data provider status
```

## Development

```bash
# Run tests
pytest

# Run linting
ruff check src/

# Run type checking
mypy src/signals_lab

# Auto-format
black src/ && isort src/
```

## License

MIT