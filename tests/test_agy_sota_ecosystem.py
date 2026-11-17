"""Property-Based (`Hypothesis`) & Full-Stack Integration Tests for `agy-sota-harness` (`L0–L12`)."""

from __future__ import annotations

import math
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

import polars as pl
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from agy_sota.invariants import (
    STUDY_WALL_DATE,
    bps_to_ratio,
    enforce_prewall_cutoff,
    hlz_dynamic_t_hurdle,
    pct_to_ratio,
    ratio_to_bps,
    validate_adr0022_stop,
    validate_ohlcv_polars_frame,
)
from agy_sota.prewall_study import evaluate_prewall_volshock_sec_shield

HARNESS_ROOT = Path(__file__).resolve().parents[1]


@settings(max_examples=150)
@given(
    entry_px=st.floats(min_value=1.00, max_value=2500.0, allow_nan=False, allow_infinity=False),
    stop_pct=st.floats(min_value=0.50, max_value=2.00, allow_nan=False, allow_infinity=False),
    side=st.sampled_from(["long", "short"]),
)
def test_adr0022_stop_never_exceeds_two_percent_property(
    entry_px: float, stop_pct: float, side: Literal["long", "short"]
) -> None:
    preset = validate_adr0022_stop(entry_px, stop_pct, side=side)
    assert 0.0 < preset.stop_distance_pct <= 2.000001
    assert 0.0 < preset.stop_distance_bps <= 200.0001
    if side == "long":
        assert preset.stop_px < preset.entry_px
    else:
        assert preset.stop_px > preset.entry_px


@pytest.mark.parametrize("bad_pct", [0.0, -1.0, 2.01, 5.0, float("nan"), float("inf")])
def test_adr0022_rejects_invalid_or_nonfinite_stops(bad_pct: float) -> None:
    with pytest.raises(ValueError):
        validate_adr0022_stop(25.0, bad_pct, side="long")


@settings(max_examples=100)
@given(bps=st.floats(min_value=-5000.0, max_value=5000.0, allow_nan=False, allow_infinity=False))
def test_dimensional_bps_ratio_roundtrip(bps: float) -> None:
    r = bps_to_ratio(bps)
    assert math.isclose(ratio_to_bps(r), bps, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(pct_to_ratio(bps / 100.0), r, rel_tol=1e-9, abs_tol=1e-9)


def test_hlz_dynamic_hurdle_strictly_monotonic() -> None:
    t1 = hlz_dynamic_t_hurdle(1)
    t10 = hlz_dynamic_t_hurdle(10)
    t100 = hlz_dynamic_t_hurdle(100)
    assert math.isclose(t1, 3.0, abs_tol=0.01)
    assert t1 < t10 < t100


def test_prewall_cutoff_guard() -> None:
    assert enforce_prewall_cutoff("2026-10-15") == STUDY_WALL_DATE
    with pytest.raises(ValueError, match="Study-Wall Violation"):
        enforce_prewall_cutoff(date(2026, 10, 16))
    assert enforce_prewall_cutoff("2026-10-16", allow_frozen_oos=True) == date(2026, 10, 16)


def test_pandera_polars_ohlcv_validation() -> None:
    good = pl.DataFrame(
        {
            "symbol": ["NVDA", "TSLA"],
            "open_px": [120.0, 250.0],
            "high_px": [125.0, 255.0],
            "low_px": [119.5, 248.0],
            "close_px": [124.0, 252.0],
            "volume_shares": [1_500_000.0, 900_000.0],
        }
    )
    out = validate_ohlcv_polars_frame(good)
    assert out.height == 2

    inverted = pl.DataFrame(
        {
            "symbol": ["BAD"],
            "open_px": [10.0],
            "high_px": [9.5],
            "low_px": [10.2],
            "close_px": [10.0],
            "volume_shares": [100.0],
        }
    )
    with pytest.raises(ValueError, match="OHLCV envelope"):
        validate_ohlcv_polars_frame(inverted)


def test_prewall_study_pit_sec_dilution_and_wall_invariants() -> None:
    start = date(2026, 2, 1)
    days = [start + timedelta(days=i) for i in range(130)]
    rows: list[dict[str, object]] = []
    for idx, d in enumerate(days):
        for sym in ("SHLD", "DILU", "BASE", "PEER"):
            px = 20.0 + 0.05 * idx
            open_px = px * 0.998
            high_px = px * 1.005
            low_px = px * 0.995
            close_px = px
            vol = 500_000.0
            # Trigger identical pre-travel volume-shock ignition on idx in (60, 70) for SHLD and DILU.
            if sym in ("SHLD", "DILU") and idx in (60, 70):
                prev_px = 20.0 + 0.05 * (idx - 1)
                close_px = prev_px * 1.04
                open_px = prev_px * 1.005
                low_px = prev_px * 1.002
                high_px = prev_px * 1.045
                vol = 2_000_000.0
            elif sym == "SHLD" and idx in (63, 73):
                close_px = px * 1.08
                high_px = close_px * 1.005
            rows.append(
                {
                    "symbol": sym,
                    "trade_date": d,
                    "raw_close": close_px,
                    "raw_volume": vol,
                    "open": open_px,
                    "high": high_px,
                    "low": low_px,
                    "close": close_px,
                    "volume": vol,
                }
            )

    daily_df = pl.DataFrame(rows)
    sec_symbols = pl.DataFrame(
        {
            "cik": [1001, 1002, 1003, 1004],
            "symbol": ["SHLD", "DILU", "BASE", "PEER"],
            "entity_type": ["operating", "operating", "operating", "operating"],
        }
    )
    # DILU files 424B5 BEFORE idx=60 (blocks both 60 & 70); SHLD files 424B5 AFTER idx=70 (must NOT look ahead!).
    sec_filings = pl.DataFrame(
        {
            "cik": [1002, 1001],
            "filed": [days[55].isoformat(), days[75].isoformat()],
            "form": ["424B5", "424B5"],
        }
    )

    res = evaluate_prewall_volshock_sec_shield(daily_df, sec_symbols, sec_filings, cumulative_trials_n=3)
    assert res.events_count == 2
    assert res.exposed_events_count == 2
    assert res.cpcv_n_paths == 5
    assert 0.0 <= res.dsr_probability <= 1.0
    assert res.shield_vs_exposed_spread_1x_bps > 0.0

    post_wall = daily_df.with_columns(
        pl.when(pl.col("trade_date") == pl.lit(days[-1]))
        .then(pl.lit(date(2026, 10, 16)))
        .otherwise(pl.col("trade_date"))
        .alias("trade_date")
    )
    with pytest.raises(ValueError, match="Study-Wall Violation"):
        evaluate_prewall_volshock_sec_shield(post_wall, sec_symbols, sec_filings, cumulative_trials_n=3)


def test_full_l0_to_l12_probes_and_merge_gate() -> None:
    p_gate = subprocess.run(
        [sys.executable, str(HARNESS_ROOT / "scripts" / "merge_gate.py")],
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    assert "AGY-MERGE-GATE PASS" in p_gate.stdout

    p_probes = subprocess.run(
        [sys.executable, str(HARNESS_ROOT / "harness" / "run_probes.py")],
        capture_output=True,
        text=True,
        timeout=35,
        check=True,
    )
    assert "13/13 probes PASSED" in p_probes.stdout
