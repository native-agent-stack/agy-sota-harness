"""SOTA Research-Convergence Contract, 7-Feed PIT DataFeed API & Strategy Template Validator.

Implements the ecosystem-wide convergence rule (`ADR-0004` / `ADR-0016`):
1. A claim or strategy lands ONLY when a 64-hex SHA-256 input snapshot, >=1 40-hex pinned
   upstream commit (`upstream-map.toml` / `~/Documents/upstream/PINS.md`), a reproducible
   command, and an `E0–E4` evidence grade agree (`other_repos_authority == 'PHILOSOPHY_ONLY'`).
2. Every equities trading lane routes `DataFeed.SIP` (`04:00–20:00 ET`) and `DataFeed.BOATS`
   (`20:00–04:00 ET` pre-`2026-12-06`, feature-flagged `23/5` SIP cutover thereafter), filters
   nominal price/liquidity on `Adjustment.RAW`, computes forward returns on `Adjustment.ALL`
   with `[-1, +3]` split-window exclusion, aligns SEC EDGAR strictly by `acceptanceDateTime`
   (`15m` half-life freshness decay + `S-3`/`424B5` dilution block), and lags FINRA `CNMSshvol`
   by `>= 1` session (`asof`).
3. Every strategy template enforces `<= 2026-10-15` pre-wall isolation, HLZ dynamic `t*(N)`,
   `5`-path purged `CPCV` (`PBO <= 0.30`), `DSR >= 0.95`, `ADVERSE_STOP_FIRST` queue priority,
   `[1.0, 2.0]` Almgren-Chriss impact survival, and paper-only `ADR-0022 <= 2.00%` stops.
"""

from __future__ import annotations

import re
import tomllib
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from agy_sota.invariants import (
    ADR0022_MAX_STOP_PCT,
    STUDY_WALL_DATE,
    hlz_dynamic_t_hurdle,
    validate_adr0022_stop,
)

NY_TZ = ZoneInfo("America/New_York")
DEC6_23X5_CUTOVER = date(2026, 12, 6)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
VALID_EVIDENCE_GRADES = frozenset({"E0", "E1", "E2", "E3", "E4"})
STRATEGY_ARCHETYPES = (
    "PRE_TRAVEL_EARLY_IGNITION",
    "FIRST_HAND_SEC_EPISODIC_PIVOT",
    "MEGA_CAP_NEAR_LOSSLESS_ORB",
    "CLIMAX_VWAP_MEAN_REVERSION",
)


def load_pinned_shelf_shas(harness_root: Path | None = None) -> dict[str, str]:
    """Load canonical 40-char upstream trading shelf commit SHAs from `upstream-map.toml`."""
    root = harness_root or Path(__file__).resolve().parents[2]
    cfg = tomllib.loads((root / "upstream-map.toml").read_text(encoding="utf-8"))
    pins = cfg.get("shelf_pins") or {}
    return {str(k): str(v) for k, v in pins.items()}


def resolve_session_datafeed(
    ts: datetime,
    *,
    enable_dec6_23x5_sip: bool = False,
) -> dict[str, Any]:
    """Resolve canonical Alpaca/IBKR session DataFeed (`sip` vs `boats`) in `America/New_York`."""
    if ts.tzinfo is None:
        raise ValueError("ts must be timezone-aware")
    ny = ts.astimezone(NY_TZ)
    ny_minutes = ny.hour * 60 + ny.minute
    if 570 <= ny_minutes < 960:
        segment = "REGULAR_RTH"
        feed = "sip"
    elif 240 <= ny_minutes < 570:
        segment = "PRE_MARKET_EXTENDED"
        feed = "sip"
    elif 960 <= ny_minutes < 1200:
        segment = "POST_MARKET_EXTENDED"
        feed = "sip"
    else:
        if enable_dec6_23x5_sip and ny.date() >= DEC6_23X5_CUTOVER:
            segment = "OVERNIGHT_23X5_SIP"
            feed = "sip"
        else:
            segment = "OVERNIGHT_BOATS"
            feed = "boats"
    return {
        "ny_iso": ny.isoformat(),
        "segment": segment,
        "alpaca_datafeed": feed,
        "ibkr_paper_port": 4002,
        "ibkr_outside_rth": segment != "REGULAR_RTH",
        "dec6_23x5_sip_enabled": enable_dec6_23x5_sip,
    }


def build_seven_feed_research_manifest(
    *,
    as_of_date: str = "2026-10-15",
    enable_dec6_23x5_sip: bool = False,
) -> dict[str, Any]:
    """Return the canonical 7-feed `sota-research-feeds.v2` PIT DataFeed specification."""
    d_asof = date.fromisoformat(as_of_date)
    return {
        "schema": "sota-research-feeds.v2",
        "as_of_date": d_asof.isoformat(),
        "study_wall_date": STUDY_WALL_DATE.isoformat(),
        "pre_wall_compliant": d_asof <= STUDY_WALL_DATE,
        "dec6_23x5_sip_enabled": enable_dec6_23x5_sip,
        "feeds": {
            "alpaca_sip": {"window_et": "04:00-20:00", "feed": "sip", "role": "Consolidated CTA/UTP tape"},
            "alpaca_boats": {
                "window_et": "20:00-04:00",
                "feed": "sip" if (enable_dec6_23x5_sip and d_asof >= DEC6_23X5_CUTOVER) else "boats",
                "role": "Blue Ocean ATS overnight venue (Dec-6 23/5 feature-flagged)",
            },
            "alpaca_raw_vs_all_adjustment": {
                "filter_adjustment": "raw",
                "return_adjustment": "all",
                "min_raw_price_usd": 2.0,
                "min_raw_dollar_vol_usd": 2_000_000.0,
            },
            "sec_edgar_acceptance_datetime": {
                "timestamp_field": "acceptanceDateTime",
                "freshness_half_life_sec": 900,
                "dilution_block_forms": ["S-3", "424B2", "424B3", "424B4", "424B5", "EFFECT"],
                "max_poll_hz": 1.0 / 15.0,
            },
            "finra_regsho_cnmsshvol_t1": {
                "min_lag_sessions": 1,
                "join_mode": "backward_asof",
                "pre_wall_max_yyyymmdd": "20261015",
            },
            "corporate_actions_split_guard": {
                "exclusion_window_sessions": [-1, 3],
                "fail_closed_on_missing_raw": True,
            },
            "ibkr_paper_4002_l1": {
                "port": 4002,
                "forbidden_live_ports": [4001, 7496],
                "max_msg_per_min": 3000,
                "max_outside_rth_spread_bps": 28.0,
            },
        },
    }


def scaffold_converged_strategy(
    strategy_id: str,
    archetype: str,
    *,
    input_package_sha256: str,
    spec_sha256: str,
    cumulative_trials_n: int = 82,
    entry_reference_px: float = 25.0,
    requested_stop_pct: float = 1.50,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Build a fail-closed SOTA Research-Converged Strategy Manifest across all 4 archetypes."""
    if archetype not in STRATEGY_ARCHETYPES:
        raise ValueError(f"Unsupported archetype {archetype!r}; expected one of {STRATEGY_ARCHETYPES}")
    stop_preset = validate_adr0022_stop(entry_reference_px, requested_stop_pct, side="long")
    pins = load_pinned_shelf_shas(harness_root)
    selected_pins = {
        k: pins[k]
        for k in (
            "alpaca-py",
            "nautilus_trader",
            "polars",
            "duckdb",
            "edgartools",
            "ml4t-diagnostic",
            "skfolio",
            "hftbacktest",
        )
        if k in pins
    }
    manifest: dict[str, Any] = {
        "schema": "sota-converged-strategy.v1",
        "strategy_id": strategy_id,
        "archetype": archetype,
        "research_convergence": {
            "input_package_sha256": input_package_sha256,
            "pinned_upstream_commits": selected_pins,
            "other_repos_authority": "PHILOSOPHY_ONLY",
            "reproducible_command": "mise exec -- uv run pytest -q",
            "evidence_grade": "E3",
        },
        "datafeed_contract": build_seven_feed_research_manifest(as_of_date=STUDY_WALL_DATE.isoformat()),
        "statistical_gates": {
            "study_wall_date": STUDY_WALL_DATE.isoformat(),
            "spec_sha256": spec_sha256,
            "cumulative_trials_n": cumulative_trials_n,
            "hlz_t_hurdle": hlz_dynamic_t_hurdle(cumulative_trials_n),
            "cpcv_paths": 5,
            "cpcv_purge_sessions": 3,
            "cpcv_embargo_sessions": 2,
            "max_pbo": 0.30,
            "min_dsr": 0.95,
            "clustered_se_by": "trade_date",
            "intrabar_tie_rule": "ADVERSE_STOP_FIRST",
            "cost_stress_multipliers": [1.0, 2.0],
        },
        "execution_and_protection": {
            "live_execution_enabled": False,
            "max_initial_stop_pct": stop_preset.stop_distance_pct,
            "reference_stop_bps": stop_preset.stop_distance_bps,
            "near_lossless_scratch_bps": [6.0, 14.0],
            "alpaca_paper": {
                "account_prefix": "PA",
                "max_req_per_min": 200,
                "exit_reserve_per_min": 15,
            },
            "ibkr_paper": {
                "account_prefix": "DU",
                "port": 4002,
                "max_msg_per_min": 3000,
            },
            "tradingview_pine_v6": {
                "version": 6,
                "calc_on_every_tick": False,
                "barstate_confirmed_only": True,
            },
        },
    }
    errors = validate_converged_strategy_manifest(manifest, harness_root=harness_root)
    if errors:
        raise ValueError(f"Generated invalid converged strategy manifest: {errors}")
    return manifest


def validate_converged_strategy_manifest(
    payload: dict[str, Any],
    *,
    harness_root: Path | None = None,
) -> list[str]:
    """Validate a SOTA strategy manifest against ADR-0004, 7-feed PIT, HLZ/CPCV/DSR, and ADR-0022."""
    errors: list[str] = []
    if payload.get("schema") != "sota-converged-strategy.v1":
        errors.append("schema must equal 'sota-converged-strategy.v1'")
    if payload.get("archetype") not in STRATEGY_ARCHETYPES:
        errors.append(f"archetype must be one of {STRATEGY_ARCHETYPES}")

    rc = payload.get("research_convergence") or {}
    if not SHA256_RE.match(str(rc.get("input_package_sha256") or "")):
        errors.append("research_convergence.input_package_sha256 must be 64-char lowercase hex SHA-256")
    if rc.get("other_repos_authority") != "PHILOSOPHY_ONLY":
        errors.append("research_convergence.other_repos_authority must equal 'PHILOSOPHY_ONLY' (ADR-0004)")
    if rc.get("evidence_grade") not in VALID_EVIDENCE_GRADES:
        errors.append("research_convergence.evidence_grade must be E0..E4")
    if not str(rc.get("reproducible_command") or "").strip():
        errors.append("research_convergence.reproducible_command must be non-empty")

    known_pins = load_pinned_shelf_shas(harness_root)
    up_pins = rc.get("pinned_upstream_commits") or {}
    if not isinstance(up_pins, dict) or not up_pins:
        errors.append("research_convergence.pinned_upstream_commits must cite >=1 40-char Git SHA")
    else:
        for repo_name, sha in up_pins.items():
            if not GIT_SHA40_RE.match(str(sha)):
                errors.append(f"upstream '{repo_name}' pin '{sha}' is not a 40-char hex Git SHA")
            elif repo_name in known_pins and known_pins[repo_name] != sha:
                errors.append(f"upstream '{repo_name}' pin drift: expected {known_pins[repo_name]}, got {sha}")

    df = payload.get("datafeed_contract") or {}
    feeds = df.get("feeds") or {}
    if df.get("schema") != "sota-research-feeds.v2":
        errors.append("datafeed_contract.schema must equal 'sota-research-feeds.v2'")
    if (feeds.get("alpaca_sip") or {}).get("feed") != "sip":
        errors.append("feeds.alpaca_sip.feed must equal 'sip'")
    if (feeds.get("alpaca_boats") or {}).get("feed") not in {"boats", "sip"}:
        errors.append("feeds.alpaca_boats.feed must be 'boats' (or Dec-6 'sip')")
    raw_all = feeds.get("alpaca_raw_vs_all_adjustment") or {}
    if raw_all.get("filter_adjustment") != "raw" or raw_all.get("return_adjustment") != "all":
        errors.append("alpaca_raw_vs_all_adjustment must filter on 'raw' and compute returns on 'all'")
    sec_cfg = feeds.get("sec_edgar_acceptance_datetime") or {}
    if sec_cfg.get("timestamp_field") != "acceptanceDateTime":
        errors.append("sec_edgar_acceptance_datetime.timestamp_field must equal 'acceptanceDateTime'")
    dil_forms = set(sec_cfg.get("dilution_block_forms") or [])
    if not {"S-3", "424B5"}.issubset(dil_forms):
        errors.append("sec_edgar_acceptance_datetime.dilution_block_forms must include 'S-3' and '424B5'")
    if int((feeds.get("finra_regsho_cnmsshvol_t1") or {}).get("min_lag_sessions") or 0) < 1:
        errors.append("finra_regsho_cnmsshvol_t1.min_lag_sessions must be >= 1")

    sg = payload.get("statistical_gates") or {}
    try:
        wall_d = date.fromisoformat(str(sg.get("study_wall_date") or ""))
        if wall_d > STUDY_WALL_DATE:
            errors.append(f"study_wall_date {wall_d} exceeds {STUDY_WALL_DATE}")
    except ValueError:
        errors.append("statistical_gates.study_wall_date must be valid ISO date <= 2026-10-15")
    if not SHA256_RE.match(str(sg.get("spec_sha256") or "")):
        errors.append("statistical_gates.spec_sha256 must be 64-char hex SHA-256")
    if float(sg.get("hlz_t_hurdle") or 0.0) < 3.0:
        errors.append("statistical_gates.hlz_t_hurdle must be >= 3.0")
    if int(sg.get("cpcv_paths") or 0) < 5 or int(sg.get("cpcv_purge_sessions") or 0) < 3:
        errors.append("CPCV requires >=5 paths and >=3 purge sessions")
    if float(sg.get("max_pbo") or 1.0) > 0.30 or float(sg.get("min_dsr") or 0.0) < 0.95:
        errors.append("statistical_gates require max_pbo <= 0.30 and min_dsr >= 0.95")
    if sg.get("intrabar_tie_rule") != "ADVERSE_STOP_FIRST":
        errors.append("statistical_gates.intrabar_tie_rule must equal 'ADVERSE_STOP_FIRST'")
    if sg.get("cost_stress_multipliers") != [1.0, 2.0]:
        errors.append("statistical_gates.cost_stress_multipliers must equal [1.0, 2.0]")

    ex = payload.get("execution_and_protection") or {}
    if ex.get("live_execution_enabled") is not False:
        errors.append("execution_and_protection.live_execution_enabled must be False (paper-only firewall)")
    stop_pct = float(ex.get("max_initial_stop_pct") or 999.0)
    if not (0.0 < stop_pct <= ADR0022_MAX_STOP_PCT + 1e-6):
        errors.append(f"max_initial_stop_pct={stop_pct} violates ADR-0022 <= {ADR0022_MAX_STOP_PCT}%")
    if int((ex.get("alpaca_paper") or {}).get("max_req_per_min") or 999) > 200:
        errors.append("alpaca_paper.max_req_per_min must be <= 200")
    ibkr_cfg = ex.get("ibkr_paper") or {}
    if ibkr_cfg.get("port") != 4002 or int(ibkr_cfg.get("max_msg_per_min") or 9999) > 3000:
        errors.append("ibkr_paper must target port 4002 with max_msg_per_min <= 3000")
    tv_cfg = ex.get("tradingview_pine_v6") or {}
    if (
        tv_cfg.get("version") != 6
        or tv_cfg.get("calc_on_every_tick") is not False
        or tv_cfg.get("barstate_confirmed_only") is not True
    ):
        errors.append(
            "tradingview_pine_v6 must enforce version==6, calc_on_every_tick==False, barstate_confirmed_only==True"
        )

    return errors
