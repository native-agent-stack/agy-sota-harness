"""Property-Based (`Hypothesis`) & Full-Stack Integration Tests for `agy-sota-harness` (`L0–L12`)."""

from __future__ import annotations

import math
import subprocess
import sys
from datetime import date
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
