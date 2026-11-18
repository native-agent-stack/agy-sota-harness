"""TDD & Hypothesis property suite for H089 Two-Stage Hybrid Entry x 50/50 Runner Convexity."""
from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from agy_sota.hybrid_runner_prewall_study import (
    H089_HYPOTHESIS_ID,
    H089_SPEC_SHA256,
    H089_TRIAL_N,
    Bar1m,
    QuoteNs,
    TradeNs,
    replay_dual_tranche_runner_convexity,
    simulate_two_stage_hybrid_entry,
)


def test_two_stage_hybrid_entry_captures_unfilled_runaway_breakout() -> None:
    """When passive bid does not fill within 120s and ask breaks above ap_entry, 50% runaway leg joins at ap_120s."""
    # Entry bid=20.00 (bs=5.0 => 500 shares), ask=20.04; price breaks higher without hitting 20.00
    quotes = (
        QuoteNs(ts_ns=60_000_000_000, bid_px=20.10, bid_lots=4.0, ask_px=20.14),
        QuoteNs(ts_ns=120_000_000_000, bid_px=20.20, bid_lots=4.0, ask_px=20.24),
    )
    trades = (TradeNs(ts_ns=30_000_000_000, price_px=20.06, size_shares=200.0),)
    res = simulate_two_stage_hybrid_entry(
        ns_entry=0,
        bp_entry=20.00,
        bs_entry=5.0,
        ap_entry=20.04,
        quotes=quotes,
        trades=trades,
    )
    assert res.participated
    assert res.mode == "runaway_join_50pct"
    assert res.weight_fraction == pytest.approx(0.50)
    assert res.avg_fill_px == pytest.approx(20.24)


def test_dual_tranche_runner_preserves_right_tail_while_core_banks_profit() -> None:
    """Core 50% harvests on pullback from +200 bps, while Runner 50% rides uncapped above +10 bps breakeven to +500 bps close."""
    bars = (
        # Bar 1: rallies +200 bps (high=102.05 -> bid_high ~102.00), arming Core Gain-Lock (+150 bps) & Runner BE (+10 bps)
        Bar1m(ts_ns=10_000_000_000, open_px=100.0, high_px=102.06, low_px=99.90, close_px=101.95),
        # Bar 2: pulls back to 101.10 (triggers Core 65% MFE lock ~101.30, while staying well above Runner +10 bps BE 100.10!)
        Bar1m(ts_ns=70_000_000_000, open_px=101.80, high_px=101.85, low_px=101.00, close_px=101.50),
        # Bar 3: afternoon continuation to 105.00 (+500 bps!)
        Bar1m(ts_ns=130_000_000_000, open_px=101.60, high_px=105.20, low_px=101.50, close_px=105.00),
    )
    out = replay_dual_tranche_runner_convexity(
        entry_px=100.00,
        fill_ts_ns=1_000_000_000,
        post_fill_quotes=(),
        intraday_bars=bars,
        close_px=105.00,
        exit_cost_1x_bps=5.0,
    )
    assert out.core_exit_reason == "core_gain_lock"
    assert out.runner_exit_reason == "runner_close_1555"
    # Combined 50/50 gross return ~ 0.5 * (+130 bps) + 0.5 * (+500 bps) = +315 bps (>> +130 bps single-tranche!)
    assert out.combined_gross_bps > 280.0


def test_adverse_stop_first_caps_downside_at_180bps_adr0022() -> None:
    bars = (Bar1m(ts_ns=10_000_000_000, open_px=100.0, high_px=104.0, low_px=97.50, close_px=97.80),)
    out = replay_dual_tranche_runner_convexity(
        entry_px=100.00,
        fill_ts_ns=1_000_000_000,
        post_fill_quotes=(),
        intraday_bars=bars,
        close_px=97.80,
        exit_cost_1x_bps=5.0,
    )
    assert out.core_exit_reason == "hard_adverse_stop_180bps"
    assert out.runner_exit_reason == "hard_adverse_stop_180bps"
    assert out.combined_gross_bps == pytest.approx(-180.0)


@given(
    entry_px=st.floats(min_value=5.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    close_mult=st.floats(min_value=0.85, max_value=1.25, allow_nan=False, allow_infinity=False),
    cost_bps=st.floats(min_value=1.0, max_value=20.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50)
def test_property_h089_cost_monotonicity_and_stop_bound(
    entry_px: float,
    close_mult: float,
    cost_bps: float,
) -> None:
    assert H089_HYPOTHESIS_ID == "H089_TWO_STAGE_HYBRID_ENTRY_X_ASYMMETRIC_RUNNER_CONVEXITY"
    assert H089_TRIAL_N == 89
    assert len(H089_SPEC_SHA256) == 64

    close_px = max(0.50, entry_px * close_mult)
    bars = (Bar1m(ts_ns=10_000, open_px=entry_px, high_px=max(entry_px, close_px), low_px=min(entry_px, close_px), close_px=close_px),)
    out = replay_dual_tranche_runner_convexity(
        entry_px=entry_px,
        fill_ts_ns=1_000,
        post_fill_quotes=(),
        intraday_bars=bars,
        close_px=close_px,
        exit_cost_1x_bps=cost_bps,
    )
    assert math.isfinite(out.combined_gross_bps)
    assert out.combined_net_2x_bps < out.combined_net_1x_bps < out.combined_gross_bps
    assert out.combined_gross_bps >= -180.0001
