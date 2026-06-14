"""Unit tests for latency percentile metrics (ticket 2.15). DB fully mocked."""

from app.services import metrics


def test_percentile_interpolates():
    values = [10, 20, 30, 40, 50]
    assert metrics._percentile(values, 50) == 30
    assert metrics._percentile(values, 95) == 48
    assert metrics._percentile(values, 99) == 50


def test_percentile_empty_is_none():
    assert metrics._percentile([], 50) is None


def test_percentile_single_value():
    assert metrics._percentile([42], 95) == 42


async def test_latency_percentiles_computes(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetch.return_value = [
        {"total_ms": 700, "stt_ms": 100, "llm_ms": 300, "tts_first_byte_ms": 200},
        {"total_ms": 900, "stt_ms": 120, "llm_ms": 400, "tts_first_byte_ms": 250},
        {"total_ms": 1100, "stt_ms": 140, "llm_ms": 500, "tts_first_byte_ms": 300},
    ]
    monkeypatch.setattr(metrics, "get_pool", lambda: pool)

    result = await metrics.latency_percentiles(limit=100)

    assert result["sample_size"] == 3
    assert result["total_ms"]["p50"] == 900
    assert result["stt_ms"]["p50"] == 120
    assert conn.fetch.await_args.args[1] == 100


async def test_latency_percentiles_skips_nulls(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetch.return_value = [
        {"total_ms": 700, "stt_ms": None, "llm_ms": 300, "tts_first_byte_ms": None},
    ]
    monkeypatch.setattr(metrics, "get_pool", lambda: pool)

    result = await metrics.latency_percentiles()

    assert result["sample_size"] == 1
    assert result["stt_ms"]["p50"] is None
    assert result["llm_ms"]["p50"] == 300


async def test_latency_percentiles_empty(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetch.return_value = []
    monkeypatch.setattr(metrics, "get_pool", lambda: pool)

    result = await metrics.latency_percentiles()

    assert result["sample_size"] == 0
    assert result["total_ms"] == {"p50": None, "p95": None, "p99": None}


async def test_latency_percentiles_swallows_error(monkeypatch):
    def _boom():
        raise RuntimeError("no pool")

    monkeypatch.setattr(metrics, "get_pool", _boom)

    result = await metrics.latency_percentiles()
    assert result["sample_size"] == 0
