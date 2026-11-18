"""Unit & Invariant Tests for `agy_sota.tick_orb_prewall_study` (`Trial N = 80`, `<= 2026-10-15`)."""

from __future__ import annotations

import math
from datetime import date, timedelta

import polars as pl
import pytest

from agy_sota.tick_orb_prewall_study import (
    evaluate_published_orb_tape_events,
    extract_orb_minute_microstructure,
)


def test_tick_orb_f_iso_vs_i_oddlot_bjzz_and_prewall_gate() -> None:
    m0 = 1_719_241_680_000_000_000
    quotes = pl.DataFrame(
        {
            "t_ns": [m0 + 1_000_000_000, m0 + 59_000_000_000],
            "bp": [100.00, 100.10],
            "ap": [100.04, 100.14],
        }
    )
    # Row 0: Odd-lot "I" buy (must NOT count as "F" ISO per meta/codes.json:88-90!)
    # Row 1: True "F" ISO buy (450 sh)
    # Row 2: Retail sub-penny x=='D' at 100.0220 (.20 cent -> excluded from BJZZ inst dark!)
    # Row 3: Midpoint x=='D' at 100.0250 (.50 cent -> counted as BJZZ inst dark!)
    # Row 4: Canceled trade (u='canceled' -> ignored!)
    trades = pl.DataFrame(
        {
            "t_ns": [
                m0 + 2_000_000_000,
                m0 + 5_000_000_000,
                m0 + 8_000_000_000,
                m0 + 10_000_000_000,
                m0 + 12_000_000_000,
            ],
            "x": ["Q", "N", "D", "D", "N"],
            "p": [100.04, 100.04, 100.0220, 100.0250, 100.04],
            "s": [50.0, 450.0, 200.0, 300.0, 9999.0],
            "c": [[" ", "I"], [" ", "F"], [" "], [" "], [" ", "F"]],
            "u": [None, None, None, None, "canceled"],
        }
    )
    feats = extract_orb_minute_microstructure(trades, quotes, m_start_ns=m0)
    assert feats is not None
    assert math.isclose(feats["minute_vol"], 1000.0, rel_tol=1e-9)
    assert math.isclose(feats["iso_f_buy_share"], 0.45, rel_tol=1e-6)
    assert math.isclose(feats["bjzz_inst_dark_share"], 0.30, rel_tol=1e-6)
    assert math.isclose(feats["ap_entry"], 100.14, rel_tol=1e-9)

    start = date(2026, 3, 1)
    days = [start + timedelta(days=i) for i in range(95)]
    d_rows = [
        {
            "symbol": s,
            "trade_date": d,
            "raw_close": 50.0 + 0.1 * i,
            "raw_volume": 500_000.0,
            "close": 50.0 + 0.1 * i,
            "volume": 500_000.0,
        }
        for i, d in enumerate(days)
        for s in ("GOOD", "PEER")
    ]
    orb_df = pl.DataFrame(
        [
            {
                "symbol": "GOOD",
                "trade_date": days[60],
                "ofi": 0.40,
                "iso_f_buy_share": 0.35,
                "bjzz_inst_dark_share": 0.20,
                "ap_entry": 55.0,
                "bp_entry": 54.95,
                "entry_spread_bps": 9.1,
            },
            {
                "symbol": "PEER",
                "trade_date": days[60],
                "ofi": -0.20,
                "iso_f_buy_share": 0.0,
                "bjzz_inst_dark_share": 0.0,
                "ap_entry": 56.0,
                "bp_entry": 55.95,
                "entry_spread_bps": 8.9,
            },
        ]
    )
    sec_syms = pl.DataFrame({"cik": [1, 2], "symbol": ["GOOD", "PEER"], "entity_type": ["operating", "operating"]})
    sec_filings = pl.DataFrame({"cik": [2], "filed": [days[40].isoformat()], "form": ["424B5"]})
    short_vol = pl.DataFrame(
        {"day": [days[59].isoformat()], "symbol": ["GOOD"], "short_volume": [600.0], "total_volume": [1000.0]}
    )
    out = evaluate_published_orb_tape_events(
        orb_df, pl.DataFrame(d_rows), sec_syms, sec_filings, short_vol, cumulative_trials_n=80
    )
    assert out.events_count == 1
    assert out.cpcv_n_paths == 5

    post_wall = orb_df.with_columns(pl.lit(date(2026, 10, 16)).alias("trade_date"))
    with pytest.raises(ValueError, match="Study-Wall Violation"):
        evaluate_published_orb_tape_events(
            post_wall, pl.DataFrame(d_rows), sec_syms, sec_filings, short_vol, cumulative_trials_n=80
        )
