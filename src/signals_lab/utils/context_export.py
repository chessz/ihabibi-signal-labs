"""Export unified context documents for Perplexity Pro / external LLM strategists."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from signals_lab import __version__
from signals_lab.config import get_settings
from signals_lab.features.registry import FeatureRegistry


def _find_project_root() -> Path:
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Could not find pyproject.toml")


def _read_excerpt(path: Path, max_lines: int | None = None, skip: int = 0) -> str:
    if not path.exists():
        return f"*(file not found: {path.name})*\n"
    lines = path.read_text(encoding="utf-8").splitlines()
    if skip:
        lines = lines[skip:]
    if max_lines is not None:
        lines = lines[:max_lines]
    return "\n".join(lines) + "\n"


def _cli_help(root: Path) -> str:
    cli = root / "bin" / "signals-lab"
    if not cli.exists():
        return "*(bin/signals-lab not found)*\n"
    try:
        result = subprocess.run(
            [str(cli), "help"],
            capture_output=True,
            text=True,
            cwd=root,
            timeout=30,
            check=False,
        )
        return result.stdout or result.stderr or ""
    except (OSError, subprocess.TimeoutExpired):
        return "*(could not capture CLI help)*\n"


def _implemented_modules(root: Path) -> str:
    pkg = root / "src" / "signals_lab"
    if not pkg.exists():
        return ""
    lines = ["| Module | Status |", "|---|---|"]
    planned = {
        "cli": "planned",
        "api": "planned",
        "evaluation": "planned",
        "workers": "planned",
        "events": "planned",
    }
    for child in sorted(pkg.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if child.name == "utils":
            status = "partial (logging, health, context export)"
        elif child.name in planned:
            status = planned[child.name]
        elif any(child.rglob("*.py")):
            status = "implemented (alpha)"
        else:
            status = "skeleton"
        lines.append(f"| `{child.name}/` | {status} |")
    return "\n".join(lines) + "\n"


def _feature_inventory() -> str:
    registry = FeatureRegistry()
    lines = ["| Feature | Family | Function |", "|---|---|---|"]
    for definition in sorted(registry.list_enabled(), key=lambda d: d.name):
        lines.append(
            f"| `{definition.name}` | {definition.family.value} | {definition.computation_function} |"
        )
    return "\n".join(lines) + f"\n\n**Total enabled:** {len(registry.list_enabled())}\n"


def _settings_snapshot() -> str:
    settings = get_settings(reload=True)
    return f"""```yaml
app:
  environment: {settings.app.environment}
ingestion:
  market: enabled={settings.ingestion.market.enabled}, interval={settings.ingestion.market.interval_seconds}s
  social: enabled={settings.ingestion.social.enabled}, interval={settings.ingestion.social.interval_seconds}s
  onchain: enabled={settings.ingestion.onchain.enabled}, interval={settings.ingestion.onchain.interval_seconds}s
  events: enabled={settings.ingestion.events.enabled}, interval={settings.ingestion.events.interval_seconds}s
features:
  windows: {settings.features.computation_windows}
  lookback_periods: {settings.features.lookback_periods}
  min_data_points: {settings.features.min_data_points}
signals:
  min_confidence_for_publish: {settings.signals.min_confidence_for_publish}
  signal_cooldown_hours: {settings.signals.signal_cooldown_hours}
workers:
  features_cron: {settings.workers.features.schedule_cron}
  signals_cron: {settings.workers.signals.schedule_cron}
  evaluation_cron: {settings.workers.evaluation.schedule_cron}
api:
  prefix: {settings.api.openapi_prefix}
  port: {settings.api.port}
```"""


def build_perplexity_context(root: Path | None = None) -> str:
    """Assemble the unified Perplexity context markdown document."""
    root = root or _find_project_root()
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    readme = _read_excerpt(root / "README.md", max_lines=40)
    specs_mission = _read_excerpt(root / "SPECS.md", max_lines=30, skip=9)
    specs_pipeline = _read_excerpt(root / "SPECS.md", max_lines=30, skip=369)
    specs_api = _read_excerpt(root / "SPECS.md", max_lines=20, skip=437)
    specs_milestones = _read_excerpt(root / "SPECS.md", max_lines=45, skip=495)
    arch_overview = _read_excerpt(root / "ARCHITECTURE.md", max_lines=35, skip=0)

    return f"""# signals-lab — Unified Context for Perplexity Pro (Strategic Brain)

> **Generated:** {now} · **Version:** {__version__} · **Regenerate:** `bin/signals-lab context export`
>
> Upload **docs/PERPLEXITY_CONTEXT.pdf** to Perplexity Pro Space (best compatibility).
> Also available: `.txt` · Regenerate: `bin/signals-lab context export pdf`

---

## 0. How to use this document (Perplexity = main brain)

**Division of labor**

| Tool | Role | Strengths |
|---|---|---|
| **Perplexity Pro** | Strategic brain | Market research, UX patterns, reliability architecture, latency budgets, competitive analysis, API/feeder design for future algo platform, prompt drafting |
| **Cursor / codebase** | Implementation | Python, tests, SPECS compliance, no-look-ahead enforcement, storage, workers |
| **signals-lab runtime** | Truth | Paper signals, metrics, health checks, provenance |

When answering, Perplexity should:
1. Ground recommendations in sections below (not generic crypto bot advice).
2. Tag every recommendation: `[MVP]` `[Stage 3]` `[Stage 4]` `[Future algo feeder]`.
3. Split **internal researcher UX** vs **downstream algo/iHabibi consumer UX**.
4. Never propose live order placement **inside signals-lab** (research boundary).
5. Propose **feeder contracts** (JSON/WebSocket) that a **separate** mini algo platform could consume later.

---

## 1. North star (reliability + speed + future feeder)

Build a **highly reliable, fast, explainable signal factory** that:

- Produces **confidence-calibrated** LONG/SHORT/WATCH candidates from multi-source data
- Publishes only **HIGH / EXTREME** bands to downstream consumers
- Tracks **paper-traded** outcomes with full provenance (reproducible, auditable)
- Serves as a **feeder layer** for a future **mini algo trading platform** (separate system)

**Reliability pillars (design for these):**
- Zero look-ahead bias (features at `t` use only data with `time ≤ t`)
- Rule + feature **versioning** on every signal (`computation_version`, `rule_version`)
- **Health checks** before ingestion (`signals-lab health apis|db`)
- **Publish gate** — LOW/MEDIUM never leak to external API
- **Cooldown** — no duplicate signals per asset within 4h
- **Walk-forward / out-of-sample** evaluation before promoting rules

**Speed targets (current config, tunable):**

| Stage | Target cadence | Notes |
|---|---|---|
| Market ingest | 60s | Binance REST/WS; fastest path to fresh OHLCV |
| Feature compute | every 15 min | `workers.features.schedule_cron` |
| Signal generate | every 5 min | `workers.signals.schedule_cron` |
| API poll (downstream) | 30–60s | Consumer-side; design for ETag + `since=` cursor |
| Future feeder | <1s push | NATS/WebSocket fan-out when `events.enabled` |

**Future mini algo platform (feeder, not executor here):**
- signals-lab exposes: signal ID, side, confidence, entry reference, stops, invalidation, expiry, provenance
- Downstream algo decides sizing, execution, risk — **outside** this repo
- Design API for **idempotent signal delivery** and **at-least-once** consumption

---

## 2. Mission & non-goals

{specs_mission}

**Non-goals (hard):**
- ❌ No live trading, exchange orders, or custody in signals-lab
- ❌ No look-ahead in features or paper eval
- ❌ No bypass of HIGH/EXTREME publish gate for external consumers

---

## 3. Architecture overview

{arch_overview}

**Pipeline (target state):**

```
Ingestion → TimescaleDB → FeatureEngine → RuleEngine → Ranking → ConfidenceCalibrator
    → Signals DB → PaperTrader → Metrics → FastAPI (+ optional NATS feeder)
```

---

## 4. What exists today (implementation truth)

### Module map

{_implemented_modules(root)}

### Feature engine (implemented)

{_feature_inventory()}

### Signal engine (partial)

| Component | Status |
|---|---|
| `RuleEngine` | ✅ Predicate tree evaluator, cooldown, regime gating |
| `ConfidenceCalibrator` | ✅ Maps score → band (LOW/MEDIUM/HIGH/EXTREME) |
| `RankingEngine` | ⬜ Planned |
| `SignalEngine` orchestration | ⬜ Planned |
| FastAPI publish layer | ⬜ Planned |

### CLI (implemented)

```text
{_cli_help(root).strip()}
```

### Health checks (implemented)

`signals-lab health apis` — Binance, NewsAPI, LunarCrush, RSS, DB connectivity

---

## 5. Active configuration snapshot

{_settings_snapshot()}

---

## 6. Signal pipeline spec (from SPECS)

{specs_pipeline}

### Publishing rule

- External API: **HIGH + EXTREME only**
- `min_confidence_for_publish` default **70**
- Every signal carries `thesis`, `contributing_factors`, `invalidation_condition`, `provenance`

---

## 7. Planned API (downstream / algo feeder)

{specs_api}

**Algo feeder requirements (propose designs for these):**
- Stable `signal_id` (UUID), monotonic `generated_at`
- `confidence_band` + numeric `confidence_score`
- `side`, `signal_class`, `regime`
- `suggested_stop`, `suggested_sell`, `expected_holding_horizon`
- `provenance.rule_version`, `provenance.data_sources`
- Pagination: `GET /signals/history?since=&asset=`
- Optional push: NATS topic `signals.generated.>` (disabled by default)

---

## 8. Milestones

{specs_milestones}

---

## 9. Data providers (cost / reliability)

| Provider | Role | Cost | Status |
|---|---|---|---|
| Binance | Market OHLCV | Free | ✅ Implemented |
| NewsAPI.org | Events/news | Free dev tier | Configured; ingest mock |
| CoinDesk/CoinTelegraph RSS | Events | Free | Health-checked |
| LunarCrush | Social sentiment | Paid | Key optional; HTTP 402 = upgrade needed |
| Glassnode | On-chain | Paid | Disabled by default |
| CryptoPanic | Events | Paid | Deprioritized |

---

## 10. Personas (always specify in prompts)

1. **Researcher** — runs CLI, tunes rules, reads paper eval metrics
2. **iHabibi / dashboard consumer** — polls API, shows signal cards to humans
3. **Mini algo platform (future)** — automated feeder consumer; needs low-latency, idempotent, structured JSON

---

## 11. Open questions for Perplexity to resolve

1. Optimal **UX** for explaining confidence bands + contributing factors to semi-technical users?
2. **Latency architecture**: 5-min signal cron vs event-driven (bar close WebSocket trigger)?
3. **Reliability**: what SLAs and circuit-breakers for a feeder used by algo trading?
4. **MVP API schema** for algo consumer — minimum fields for safe paper → live handoff (in downstream system)?
5. **Feature set** for fast intraday signals vs slower swing signals — tradeoffs?
6. **Competitive patterns** from TradingView, 3Commas, Nansen, Messari — what to adopt/avoid?

---

## 12. Prompt template (paste into Perplexity thread)

```
Context: uploaded signals-lab unified spec.
Persona: [Researcher | iHabibi dashboard | Mini algo feeder]
Goal: [one sentence]
Constraints: no live trading in signals-lab; HIGH/EXTREME publish only; no look-ahead.

Deliver:
1. Recommendation (tag MVP / Stage 3 / Future feeder)
2. UX or API sketch
3. Reliability & latency notes
4. What to implement in Cursor next (files/modules)
5. Risks & mitigations
```

---

## 13. README excerpt

{readme}

---

*End of unified context — regenerate after major milestones.*
"""


def export_context(
    output_path: Path | None = None,
    root: Path | None = None,
    *,
    fmt: str = "md",
) -> Path:
    """Write context document and return its path.

    fmt: ``md`` (default), ``txt``, or ``pdf`` path hint only — use ``export_context_pdf()`` for PDF.
    """
    root = root or _find_project_root()
    docs_dir = root / "docs"
    docs_dir.mkdir(exist_ok=True)

    if output_path is not None:
        destination = output_path
    elif fmt == "txt":
        destination = docs_dir / "PERPLEXITY_CONTEXT.txt"
    else:
        destination = docs_dir / "PERPLEXITY_CONTEXT.md"

    content = build_perplexity_context(root)
    destination.write_text(content, encoding="utf-8")
    return destination


def export_all_formats(root: Path | None = None) -> list[Path]:
    """Export .md, .txt, and .pdf versions."""
    root = root or _find_project_root()
    return [
        export_context(root=root, fmt="md"),
        export_context(root=root, fmt="txt"),
        export_context_pdf(root=root),
    ]


def _find_unicode_font() -> Path | None:
    """Locate a TTF font that supports UTF-8 (for PDF export)."""
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def _export_pdf_via_pandoc(content: str, destination: Path) -> bool:
    """Try pandoc markdown→PDF. Returns True on success."""
    import shutil
    import tempfile

    if shutil.which("pandoc") is None:
        return False

    with tempfile.TemporaryDirectory() as tmp:
        md_path = Path(tmp) / "context.md"
        md_path.write_text(content, encoding="utf-8")
        try:
            subprocess.run(
                [
                    "pandoc",
                    str(md_path),
                    "-o",
                    str(destination),
                    "-V",
                    "geometry:margin=1in",
                    "-V",
                    "fontsize=10pt",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return destination.is_file() and destination.stat().st_size > 0
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False


def _export_pdf_via_fpdf2(content: str, destination: Path) -> None:
    """Render plain-text PDF with Unicode support via fpdf2."""
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise RuntimeError(
            "PDF export requires fpdf2. Run: pip install fpdf2  "
            "(included in pip install -e \".[docs]\")"
        ) from exc

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_path = _find_unicode_font()
    if font_path is not None:
        pdf.add_font("DejaVu", "", str(font_path))
        pdf.set_font("DejaVu", size=9)
    else:
        pdf.set_font("Helvetica", size=9)
        content = content.encode("ascii", errors="replace").decode("ascii")

    line_height = 4.5
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin

    for line in content.splitlines():
        text = line if line.strip() else " "
        # Strip markdown bold markers for cleaner PDF text extraction
        text = text.replace("**", "")
        try:
            pdf.multi_cell(usable_width, line_height, text)
        except Exception:
            safe = text.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(usable_width, line_height, safe)

    pdf.output(str(destination))


def export_context_pdf(
    output_path: Path | None = None,
    root: Path | None = None,
) -> Path:
    """Write PERPLEXITY_CONTEXT.pdf for Perplexity Spaces upload."""
    root = root or _find_project_root()
    docs_dir = root / "docs"
    docs_dir.mkdir(exist_ok=True)
    destination = output_path or docs_dir / "PERPLEXITY_CONTEXT.pdf"
    content = build_perplexity_context(root)

    if _export_pdf_via_pandoc(content, destination):
        return destination

    _export_pdf_via_fpdf2(content, destination)
    return destination


def main() -> None:
    root = _find_project_root()
    path = export_context(root=root)
    print(str(path))


if __name__ == "__main__":
    main()
