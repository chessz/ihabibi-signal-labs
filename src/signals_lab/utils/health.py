"""Health checks for external APIs, RSS feeds, and databases."""

# ruff: noqa: PLR0911

from __future__ import annotations

import asyncio
import os
import sys
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import httpx

from signals_lab.config import Settings, get_settings

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment,misc]

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[assignment,misc]

_HTTP_OK = 200
_HTTP_PAYMENT_REQUIRED = 402


class HealthStatus(StrEnum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass(frozen=True)
class HealthCheckResult:
    name: str
    category: str
    status: HealthStatus
    message: str
    latency_ms: int | None = None


def _load_dotenv(project_root: Path | None = None) -> None:
    """Load .env from project root when python-dotenv is available."""
    if load_dotenv is None:
        return
    root = project_root or _find_project_root()
    env_file = root / ".env"
    if env_file.exists():
        load_dotenv(env_file)


def _find_project_root() -> Path:
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return current


def _env_key(name: str | None) -> str | None:
    if not name:
        return None
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("your_"):
        return None
    return value


async def _timed_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs: object,
) -> tuple[int, int]:
    start = time.perf_counter()
    response = await client.request(method, url, **kwargs)
    latency_ms = int((time.perf_counter() - start) * 1000)
    return response.status_code, latency_ms


class HealthChecker:
    """Run connectivity and credential checks for signals-lab dependencies."""

    def __init__(self, settings: Settings | None = None, project_root: Path | None = None) -> None:
        self._root = project_root or _find_project_root()
        _load_dotenv(self._root)
        self._settings = settings or get_settings(reload=True)

    async def run_all(self) -> list[HealthCheckResult]:
        results: list[HealthCheckResult] = []
        results.append(self.check_config())
        results.extend(await self.run_apis())
        results.extend(await self.run_db())
        return results

    async def run_apis(self) -> list[HealthCheckResult]:
        results: list[HealthCheckResult] = []
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            tasks: list[tuple[str, Callable[[httpx.AsyncClient], Coroutine[object, object, HealthCheckResult]]]] = [
                ("binance", self._check_binance),
                ("newsapi", self._check_newsapi),
                ("lunarcrush", self._check_lunarcrush),
                ("glassnode", self._check_glassnode),
                ("cryptopanic", self._check_cryptopanic),
                ("coindesk_rss", self._check_coindesk_rss),
                ("cointelegraph_rss", self._check_cointelegraph_rss),
            ]
            for _name, check_fn in tasks:
                try:
                    results.append(await check_fn(client))
                except Exception as exc:
                    results.append(
                        HealthCheckResult(
                            name=_name,
                            category="api",
                            status=HealthStatus.FAIL,
                            message=f"unexpected error: {exc}",
                        )
                    )
        return results

    async def run_db(self) -> list[HealthCheckResult]:
        results: list[HealthCheckResult] = []
        results.append(await self._check_postgres("timescale_db", self._settings.storage.timeseries.url))
        results.append(await self._check_postgres("relational_db", self._settings.storage.relational.url))
        return results

    def check_config(self) -> HealthCheckResult:
        try:
            env = self._settings.app.environment
            return HealthCheckResult(
                name="config",
                category="config",
                status=HealthStatus.OK,
                message=f"settings loaded (environment={env})",
            )
        except Exception as exc:
            return HealthCheckResult(
                name="config",
                category="config",
                status=HealthStatus.FAIL,
                message=str(exc),
            )

    async def _check_binance(self, client: httpx.AsyncClient) -> HealthCheckResult:
        if not self._settings.ingestion.market.enabled:
            return HealthCheckResult("binance", "api", HealthStatus.SKIP, "market ingestion disabled")

        base_url = "https://api.binance.com"
        for provider in self._settings.ingestion.market.providers:
            if provider.name == "binance" and provider.base_url:
                base_url = provider.base_url.rstrip("/")
                break

        try:
            status_code, latency_ms = await _timed_request(client, "GET", f"{base_url}/api/v3/ping")
            if status_code == _HTTP_OK:
                return HealthCheckResult("binance", "api", HealthStatus.OK, "ping OK", latency_ms)
            return HealthCheckResult(
                "binance", "api", HealthStatus.FAIL, f"HTTP {status_code}", latency_ms
            )
        except httpx.HTTPError as exc:
            return HealthCheckResult("binance", "api", HealthStatus.FAIL, str(exc))

    async def _check_newsapi(self, client: httpx.AsyncClient) -> HealthCheckResult:  # noqa: PLR0911
        if not self._settings.ingestion.events.enabled:
            return HealthCheckResult("newsapi", "api", HealthStatus.SKIP, "events ingestion disabled")

        api_key = None
        for provider in self._settings.ingestion.events.providers:
            if provider.name == "newsapi":
                api_key = _env_key(provider.api_key_env)
                base_url = (provider.base_url or "https://newsapi.org/v2").rstrip("/")
                break
        else:
            return HealthCheckResult("newsapi", "api", HealthStatus.SKIP, "not configured")

        if not api_key:
            return HealthCheckResult(
                "newsapi",
                "api",
                HealthStatus.WARN,
                "NEWSAPI_KEY not set — get one at https://newsapi.org",
            )

        try:
            status_code, latency_ms = await _timed_request(
                client,
                "GET",
                f"{base_url}/top-headlines",
                params={"country": "us", "pageSize": 1, "apiKey": api_key},
            )
            if status_code == _HTTP_OK:
                return HealthCheckResult("newsapi", "api", HealthStatus.OK, "top-headlines OK", latency_ms)
            if status_code in (401, 403):
                return HealthCheckResult("newsapi", "api", HealthStatus.FAIL, "invalid API key", latency_ms)
            return HealthCheckResult("newsapi", "api", HealthStatus.FAIL, f"HTTP {status_code}", latency_ms)
        except httpx.HTTPError as exc:
            return HealthCheckResult("newsapi", "api", HealthStatus.FAIL, str(exc))

    async def _check_lunarcrush(self, client: httpx.AsyncClient) -> HealthCheckResult:  # noqa: PLR0911
        if not self._settings.ingestion.social.enabled:
            return HealthCheckResult("lunarcrush", "api", HealthStatus.SKIP, "social ingestion disabled")

        api_key = None
        for provider in self._settings.ingestion.social.providers:
            if provider.name == "lunarcrush":
                api_key = _env_key(provider.api_key_env)
                break

        if not api_key:
            return HealthCheckResult(
                "lunarcrush",
                "api",
                HealthStatus.WARN,
                "LUNARCRUSH_API_KEY not set — https://lunarcrush.com/developers",
            )

        # v4 API (current); config still references legacy v2 base URL
        url = "https://lunarcrush.com/api4/public/topic/bitcoin/v1"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            status_code, latency_ms = await _timed_request(client, "GET", url, headers=headers)
            if status_code == _HTTP_OK:
                return HealthCheckResult("lunarcrush", "api", HealthStatus.OK, "topic/bitcoin OK", latency_ms)
            if status_code in (401, 403):
                return HealthCheckResult("lunarcrush", "api", HealthStatus.FAIL, "invalid API key", latency_ms)
            if status_code == _HTTP_PAYMENT_REQUIRED:
                return HealthCheckResult(
                    "lunarcrush",
                    "api",
                    HealthStatus.WARN,
                    "subscription required (HTTP 402) — check plan at lunarcrush.com",
                    latency_ms,
                )
            return HealthCheckResult("lunarcrush", "api", HealthStatus.FAIL, f"HTTP {status_code}", latency_ms)
        except httpx.HTTPError as exc:
            return HealthCheckResult("lunarcrush", "api", HealthStatus.FAIL, str(exc))

    async def _check_glassnode(self, client: httpx.AsyncClient) -> HealthCheckResult:
        if not self._settings.ingestion.onchain.enabled:
            return HealthCheckResult("glassnode", "api", HealthStatus.SKIP, "onchain ingestion disabled")

        api_key = None
        base_url = "https://api.glassnode.com/v1"
        for provider in self._settings.ingestion.onchain.providers:
            if provider.name == "glassnode":
                api_key = _env_key(provider.api_key_env)
                if provider.base_url:
                    base_url = provider.base_url.rstrip("/")
                break

        if not api_key:
            return HealthCheckResult(
                "glassnode",
                "api",
                HealthStatus.WARN,
                "GLASSNODE_API_KEY not set (onchain disabled in practice)",
            )

        try:
            status_code, latency_ms = await _timed_request(
                client,
                "GET",
                f"{base_url}/metrics/market/price_usd_close",
                params={"a": "BTC", "api_key": api_key, "i": "24h"},
            )
            if status_code == _HTTP_OK:
                return HealthCheckResult("glassnode", "api", HealthStatus.OK, "BTC price metric OK", latency_ms)
            if status_code in (401, 403):
                return HealthCheckResult("glassnode", "api", HealthStatus.FAIL, "invalid API key", latency_ms)
            return HealthCheckResult("glassnode", "api", HealthStatus.FAIL, f"HTTP {status_code}", latency_ms)
        except httpx.HTTPError as exc:
            return HealthCheckResult("glassnode", "api", HealthStatus.FAIL, str(exc))

    async def _check_cryptopanic(self, client: httpx.AsyncClient) -> HealthCheckResult:
        configured = any(p.name == "cryptopanic" for p in self._settings.ingestion.events.providers)
        if not configured:
            return HealthCheckResult("cryptopanic", "api", HealthStatus.SKIP, "not in config")

        api_key = _env_key("CRYPTOPANIC_API_KEY")
        if not api_key:
            return HealthCheckResult(
                "cryptopanic",
                "api",
                HealthStatus.WARN,
                "CRYPTOPANIC_API_KEY not set (free tier discontinued — consider RSS/NewsAPI)",
            )

        try:
            status_code, latency_ms = await _timed_request(
                client,
                "GET",
                "https://cryptopanic.com/api/v1/posts/",
                params={"auth_token": api_key, "public": "true"},
            )
            if status_code == _HTTP_OK:
                return HealthCheckResult("cryptopanic", "api", HealthStatus.OK, "posts OK", latency_ms)
            if status_code in (401, 403):
                return HealthCheckResult("cryptopanic", "api", HealthStatus.FAIL, "invalid or expired API key", latency_ms)
            return HealthCheckResult("cryptopanic", "api", HealthStatus.FAIL, f"HTTP {status_code}", latency_ms)
        except httpx.HTTPError as exc:
            return HealthCheckResult("cryptopanic", "api", HealthStatus.FAIL, str(exc))

    async def _check_coindesk_rss(self, client: httpx.AsyncClient) -> HealthCheckResult:
        url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        try:
            status_code, latency_ms = await _timed_request(client, "GET", url)
            if status_code == _HTTP_OK:
                return HealthCheckResult("coindesk_rss", "rss", HealthStatus.OK, "feed reachable", latency_ms)
            return HealthCheckResult("coindesk_rss", "rss", HealthStatus.FAIL, f"HTTP {status_code}", latency_ms)
        except httpx.HTTPError as exc:
            return HealthCheckResult("coindesk_rss", "rss", HealthStatus.FAIL, str(exc))

    async def _check_cointelegraph_rss(self, client: httpx.AsyncClient) -> HealthCheckResult:
        url = "https://cointelegraph.com/rss"
        try:
            status_code, latency_ms = await _timed_request(client, "GET", url)
            if status_code == _HTTP_OK:
                return HealthCheckResult("cointelegraph_rss", "rss", HealthStatus.OK, "feed reachable", latency_ms)
            return HealthCheckResult("cointelegraph_rss", "rss", HealthStatus.FAIL, f"HTTP {status_code}", latency_ms)
        except httpx.HTTPError as exc:
            return HealthCheckResult("cointelegraph_rss", "rss", HealthStatus.FAIL, str(exc))

    async def _check_postgres(self, name: str, url: str) -> HealthCheckResult:
        if asyncpg is None:
            return HealthCheckResult(name, "db", HealthStatus.FAIL, "asyncpg not installed — run ./setup.sh")

        start = time.perf_counter()
        try:
            conn = await asyncpg.connect(url, timeout=5)
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            latency_ms = int((time.perf_counter() - start) * 1000)
            short_version = (version or "connected").split(",")[0]
            return HealthCheckResult(name, "db", HealthStatus.OK, short_version, latency_ms)
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return HealthCheckResult(name, "db", HealthStatus.FAIL, str(exc), latency_ms)


def format_results(results: list[HealthCheckResult]) -> str:
    """Render health results as a fixed-width table."""
    lines = [f"{'STATUS':<6} {'CHECK':<18} {'CATEGORY':<8}  DETAIL", "-" * 72]
    for result in results:
        latency = f" ({result.latency_ms}ms)" if result.latency_ms is not None else ""
        lines.append(
            f"{result.status.value:<6} {result.name:<18} {result.category:<8}  "
            f"{result.message}{latency}"
        )
    return "\n".join(lines)


def summarize_results(results: list[HealthCheckResult]) -> tuple[int, int, int, int]:
    ok = sum(1 for r in results if r.status == HealthStatus.OK)
    warn = sum(1 for r in results if r.status == HealthStatus.WARN)
    fail = sum(1 for r in results if r.status == HealthStatus.FAIL)
    skip = sum(1 for r in results if r.status == HealthStatus.SKIP)
    return ok, warn, fail, skip


async def run_health_checks(scope: str = "all", project_root: Path | None = None) -> int:
    """Run health checks and return process exit code (0 = no failures)."""
    checker = HealthChecker(project_root=project_root)
    if scope == "apis":
        results = [checker.check_config(), *await checker.run_apis()]
    elif scope == "db":
        results = [checker.check_config(), *await checker.run_db()]
    else:
        results = await checker.run_all()

    print(format_results(results))
    ok, warn, fail, skip = summarize_results(results)
    print()
    print(f"Summary: {ok} ok, {warn} warn, {fail} fail, {skip} skip")
    return 1 if fail > 0 else 0


def main() -> None:
    scope = sys.argv[1] if len(sys.argv) > 1 else "all"
    exit_code = asyncio.run(run_health_checks(scope=scope))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
