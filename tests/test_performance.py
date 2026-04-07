"""
Performance tests for the FinBot REST API.

These tests measure real end-to-end response times against a running server
and assert that each endpoint stays within acceptable latency thresholds.

Requirements:
    Set in .env or environment before running:
        PERF_TEST_BASE_URL  — base URL of the server (default: http://localhost:8000)
        PERF_TEST_TOKEN     — valid Supabase JWT for authentication

Run only performance tests:
    pytest tests/test_performance.py -v -m performance

Skip in regular test runs:
    pytest tests/ -m "not performance"
"""
import os
import statistics
import time

import httpx
import pytest

BASE_URL = os.getenv("PERF_TEST_BASE_URL", "http://localhost:8000")
TOKEN = os.getenv("PERF_TEST_TOKEN", "")

pytestmark = pytest.mark.performance

# ── Thresholds (seconds) ────────────────────────────────────────────────────
THRESHOLD_HEALTH = 0.10       # 100ms  — no DB
THRESHOLD_CATEGORIES = 0.50   # 500ms  — simple list query
THRESHOLD_EXPENSES = 0.80     # 800ms  — paginated query with join
THRESHOLD_REPORTS_SUMMARY = 0.80   # 800ms  — aggregate by category
THRESHOLD_REPORTS_MONTHLY = 1.00   # 1000ms — full year aggregation
THRESHOLD_EXPORT = 1.00       # 1000ms — CSV generation

RUNS = 5  # number of repetitions per endpoint for stable measurement


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client() -> httpx.Client:
    """HTTP client pointed at the running server. Skips if server is unreachable."""
    try:
        with httpx.Client(base_url=BASE_URL, timeout=3.0) as c:
            c.get("/health")  # connectivity check
            yield c
    except httpx.ConnectError:
        pytest.skip(f"Server not reachable at {BASE_URL} — start the server before running performance tests")


@pytest.fixture(scope="module")
def auth_headers() -> dict:
    if not TOKEN:
        pytest.skip("PERF_TEST_TOKEN not set — add PERF_TEST_TOKEN to .env")
    return {"Authorization": f"Bearer {TOKEN}"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def measure(client: httpx.Client, method: str, url: str, runs: int = RUNS, **kwargs) -> dict:
    """
    Call an endpoint `runs` times and return timing statistics.
    Raises AssertionError immediately if any request returns a non-2xx status.
    """
    durations = []
    for _ in range(runs):
        start = time.perf_counter()
        response = getattr(client, method)(url, **kwargs)
        elapsed = time.perf_counter() - start
        assert response.status_code < 300, (
            f"{method.upper()} {url} returned {response.status_code}: {response.text[:200]}"
        )
        durations.append(elapsed)

    return {
        "min": min(durations),
        "max": max(durations),
        "mean": statistics.mean(durations),
        "median": statistics.median(durations),
        "p95": sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else max(durations),
        "runs": durations,
    }


def assert_threshold(stats: dict, threshold: float, label: str) -> None:
    """Assert median is under threshold and print a timing summary."""
    median = stats["median"]
    print(
        f"\n  {label}: "
        f"median={median*1000:.0f}ms  "
        f"min={stats['min']*1000:.0f}ms  "
        f"max={stats['max']*1000:.0f}ms  "
        f"(threshold={threshold*1000:.0f}ms)"
    )
    assert median <= threshold, (
        f"{label} median {median*1000:.0f}ms exceeds threshold {threshold*1000:.0f}ms\n"
        f"  All samples (ms): {[round(r*1000) for r in stats['runs']]}"
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_health_endpoint_response_time(client):
    """/health should respond in under 100ms — no DB involved."""
    stats = measure(client, "get", "/health", runs=10)
    assert_threshold(stats, THRESHOLD_HEALTH, "GET /health")


def test_list_expenses_response_time(client, auth_headers):
    """GET /api/expenses should paginate and respond under 800ms."""
    stats = measure(
        client, "get", "/api/expenses",
        headers=auth_headers,
        params={"page": 1, "page_size": 20},
    )
    assert_threshold(stats, THRESHOLD_EXPENSES, "GET /api/expenses")


def test_list_expenses_with_filters_response_time(client, auth_headers):
    """Filtering expenses by date range and category should stay under 800ms."""
    stats = measure(
        client, "get", "/api/expenses",
        headers=auth_headers,
        params={
            "start": "2025-01-01",
            "end": "2025-12-31",
            "page": 1,
            "page_size": 20,
        },
    )
    assert_threshold(stats, THRESHOLD_EXPENSES, "GET /api/expenses?start=&end=")


def test_list_categories_response_time(client, auth_headers):
    """GET /api/categories should respond under 500ms."""
    stats = measure(client, "get", "/api/categories", headers=auth_headers)
    assert_threshold(stats, THRESHOLD_CATEGORIES, "GET /api/categories")


def test_reports_summary_response_time(client, auth_headers):
    """GET /api/reports/summary should aggregate and respond under 800ms."""
    stats = measure(
        client, "get", "/api/reports/summary",
        headers=auth_headers,
        params={"start": "2025-01-01", "end": "2025-12-31"},
    )
    assert_threshold(stats, THRESHOLD_REPORTS_SUMMARY, "GET /api/reports/summary")


def test_reports_monthly_response_time(client, auth_headers):
    """GET /api/reports/monthly should aggregate a full year under 1000ms."""
    stats = measure(
        client, "get", "/api/reports/monthly",
        headers=auth_headers,
        params={"year": 2025},
    )
    assert_threshold(stats, THRESHOLD_REPORTS_MONTHLY, "GET /api/reports/monthly")


def test_export_csv_response_time(client, auth_headers):
    """GET /api/export/csv should generate and respond under 1000ms."""
    stats = measure(
        client, "get", "/api/export/csv",
        headers=auth_headers,
        params={"start": "2025-01-01", "end": "2025-12-31"},
    )
    assert_threshold(stats, THRESHOLD_EXPORT, "GET /api/export/csv")


def test_auth_validation_response_time(client, auth_headers):
    """
    Measure the overhead of JWT validation against Supabase.
    If this is slow (> 300ms), the bottleneck is likely auth, not business logic.
    """
    stats = measure(client, "get", "/api/categories", headers=auth_headers, runs=10)
    auth_threshold = 0.30
    print(
        f"\n  Auth overhead estimate (categories endpoint): "
        f"median={stats['median']*1000:.0f}ms"
    )
    # Soft assertion — prints a warning instead of failing if above threshold
    if stats["median"] > auth_threshold:
        print(
            f"\n  ⚠ WARNING: auth validation median {stats['median']*1000:.0f}ms "
            f"exceeds {auth_threshold*1000:.0f}ms — consider caching get_user() calls"
        )
