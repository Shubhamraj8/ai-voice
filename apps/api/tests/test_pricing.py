"""Tests for pricing plans (ticket 5.01). DB mocked, no pipecat import."""

import uuid

from app.services import pricing


def _row(key, name, price, minutes, overage, numbers, order):
    return {
        "id": uuid.uuid4(),
        "key": key,
        "name": name,
        "price_inr_month": price,
        "included_minutes": minutes,
        "overage_inr_per_min": overage,
        "phone_numbers": numbers,
        "active": True,
        "sort_order": order,
    }


async def test_list_pricing_plans_returns_models(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pricing, "get_pool", lambda: pool)
    conn.fetch.return_value = [
        _row("starter", "Starter", 2999, 300, 15, 1, 1),
        _row("growth", "Growth", 6999, 800, 13, 1, 2),
        _row("pro", "Pro", 16999, 2000, 12, 2, 3),
    ]

    plans = await pricing.list_pricing_plans()

    assert [p.key for p in plans] == ["starter", "growth", "pro"]
    assert plans[0].price_inr_month == 2999
    assert plans[2].included_minutes == 2000
    assert plans[2].phone_numbers == 2
    # active_only filters in the query
    assert "active = true" in conn.fetch.await_args.args[0]


async def test_list_pricing_plans_all_when_not_active_only(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pricing, "get_pool", lambda: pool)
    conn.fetch.return_value = []

    await pricing.list_pricing_plans(active_only=False)

    assert "active = true" not in conn.fetch.await_args.args[0]
