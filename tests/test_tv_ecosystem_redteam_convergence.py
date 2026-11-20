"""Tests & Hypothesis Proofs for `ADR-0036` TradingView Ecosystem Red-Team Convergence."""

from __future__ import annotations

from typing import Any, cast

from hypothesis import given, settings
from hypothesis import strategies as st

from agy_sota.tv_ecosystem_redteam_convergence import (
    EXPECTED_MULTI_LAYOUT_IDS,
    EXPECTED_TV_LIBRARIES,
    run_tv_ecosystem_redteam_probes,
    verify_largecap_trail_and_rate_bounds,
    verify_tv_manifest_governance,
)


def _clean_manifest() -> dict:
    return {
        "order_authority_on_visual_surfaces": False,
        "visual_artifacts_may_bind_alert_or_webhook": False,
        "standalone_alpha_claim": False,
        "tv_library_landscape": [
            {
                "library_id": lid,
                "capability_class": cls,
                "order_authority": False,
                "visual_may_bind_webhook": False,
            }
            for lid, cls in EXPECTED_TV_LIBRARIES
        ],
        "multi_layouts": [
            {
                "layout_id": ly_id,
                "unobstructed_candle_area_min_pct": 92.5,
                "order_authority": False,
            }
            for ly_id in EXPECTED_MULTI_LAYOUT_IDS
        ],
    }


def test_redteam_probes_all_pass_with_clean_manifest() -> None:
    report = run_tv_ecosystem_redteam_probes(manifest=_clean_manifest())
    assert report["all_passed"] is True
    assert report["probes_passed"] == report["probes_total"] == 8
    assert len(report["report_sha256"]) == 64


def test_manifest_governance_catches_privacy_and_authority_violations() -> None:
    bad = _clean_manifest()
    bad["order_authority_on_visual_surfaces"] = True
    bad["multi_layouts"][0]["unobstructed_candle_area_min_pct"] = 80.0
    bad["leaked_note"] = "PA" + "1234567890"
    ok, errs = verify_tv_manifest_governance(bad)
    assert ok is False
    assert "VISUAL_ORDER_AUTHORITY_MUST_BE_FALSE" in errs
    assert any("CANDLE_OBSTRUCTION" in e for e in errs)
    assert "PRIVACY_LEAK:alpaca_pa_id" in errs


def test_manifest_governance_closes_p1_rogue_library_per_lib_authority_and_nan_bypasses() -> None:
    # PoC 1: Per-library order_authority=True & visual_may_bind_webhook=True must fail closed
    m_auth = _clean_manifest()
    m_auth["tv_library_landscape"][0]["order_authority"] = True
    m_auth["tv_library_landscape"][0]["visual_may_bind_webhook"] = True
    ok_a, errs_a = verify_tv_manifest_governance(m_auth)
    assert ok_a is False
    assert any("LIBRARY_ORDER_AUTHORITY_MUST_BE_FALSE" in e for e in errs_a)
    assert any("LIBRARY_WEBHOOK_BINDING_MUST_BE_FALSE" in e for e in errs_a)

    # PoC 2: Appending an unregistered rogue library or duplicate library must fail closed
    m_rogue = _clean_manifest()
    m_rogue["tv_library_landscape"].append(
        {
            "library_id": "rogue-signalstack",
            "capability_class": "PINNED_INTEGRATE",
            "order_authority": False,
            "visual_may_bind_webhook": False,
        }
    )
    ok_r, errs_r = verify_tv_manifest_governance(m_rogue)
    assert ok_r is False
    assert "UNREGISTERED_LIBRARY_ID:rogue-signalstack" in errs_r

    # PoC 3: NaN or bool unobstructed_candle_area_min_pct must fail closed (never silently pass)
    m_nan = _clean_manifest()
    m_nan["multi_layouts"][0]["unobstructed_candle_area_min_pct"] = float("nan")
    ok_n, errs_n = verify_tv_manifest_governance(m_nan)
    assert ok_n is False
    assert any("CANDLE_OBSTRUCTION" in e for e in errs_n)
    assert "NONFINITE_OR_UNSERIALIZABLE_MANIFEST" in errs_n

    # PoC 4: Reserve exceeding max_rpm and NaN rpm must fail closed
    ok_rpm, errs_rpm = verify_largecap_trail_and_rate_bounds(
        trail_bps=8.5,
        be_arm_bps=6.0,
        initial_stop_pct=1.25,
        alpaca_max_rpm=1000,
        alpaca_exit_reserve_rpm=1200,
        ibkr_port=4002,
        ibkr_max_mpm=3000,
        ibkr_exit_reserve_mpm=300,
    )
    assert ok_rpm is False
    assert any("ALPACA_EXIT_RESERVE_EXCEEDS_MAX" in e for e in errs_rpm)

    ok_nan_rpm, errs_nan_rpm = verify_largecap_trail_and_rate_bounds(
        trail_bps=8.5,
        be_arm_bps=6.0,
        initial_stop_pct=1.25,
        alpaca_max_rpm=1000,
        alpaca_exit_reserve_rpm=cast(Any, float("nan")),
        ibkr_port=4002,
        ibkr_max_mpm=3000,
        ibkr_exit_reserve_mpm=300,
    )
    assert ok_nan_rpm is False and errs_nan_rpm

    # PoC 5: Manifest injecting live IBKR port 4001, low IBKR reserve, live paper_lanes, or TP-enabled preset fails closed
    m_live_port = _clean_manifest()
    m_live_port["dual_lane_1000rpm_budget"] = {
        "ibkr_paper_port": 4001,
        "alpaca_algo_plus_rpm": 1000,
        "alpaca_exit_reserve_rpm": 100,
        "ibkr_paper_max_mpm": 3000,
        "ibkr_paper_exit_reserve_mpm": 10,
    }
    m_live_port["multi_layouts"][0]["lossless_binding"] = {"paper_lanes": ["LIVE:8798", "IBKR:4001"]}
    m_live_port["uncapped_quickbar_presets"] = [
        {"chip": "[B]", "tp_enabled": True, "quantity_type": "Shares", "sl_pct_price": 1.60}
    ]
    ok_lp, errs_lp = verify_tv_manifest_governance(m_live_port)
    assert ok_lp is False
    assert "MANIFEST_IBKR_LIVE_PORT_REFUSED:4001" in errs_lp
    assert any("MANIFEST_INVALID_IBKR_RATE_BUDGET" in e for e in errs_lp)
    assert any("LAYOUT_LIVE_LANE_FORBIDDEN" in e for e in errs_lp)
    assert any("MANIFEST_PRESET_FIXED_TP_FORBIDDEN" in e for e in errs_lp)


@settings(max_examples=500, deadline=None)
@given(
    trail_bps=st.floats(min_value=6.0, max_value=14.0, allow_nan=False, allow_infinity=False),
    be_arm_bps=st.floats(min_value=5.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    initial_stop_pct=st.floats(min_value=0.05, max_value=2.00, allow_nan=False, allow_infinity=False),
)
def test_hypothesis_valid_largecap_and_1000rpm_bounds(
    trail_bps: float,
    be_arm_bps: float,
    initial_stop_pct: float,
) -> None:
    ok, errs = verify_largecap_trail_and_rate_bounds(
        trail_bps=trail_bps,
        be_arm_bps=be_arm_bps,
        initial_stop_pct=initial_stop_pct,
        alpaca_max_rpm=1000,
        alpaca_exit_reserve_rpm=100,
        ibkr_port=4002,
        ibkr_max_mpm=3000,
        ibkr_exit_reserve_mpm=300,
        take_profit_cap_enabled=False,
    )
    assert ok is True and errs == []
