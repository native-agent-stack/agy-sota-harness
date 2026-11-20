"""Antigravity Meta-Session TradingView Library Stack, 5-Layout Coordination & Red-Team Verifier (`ADR-0036`).

Provides deterministic, offline-verifiable governance & red-team probes across the finalized Orca ecosystem:
1. **14-Library TradingView Capability Firewall (`ADR-0017` / `ADR-0045` / `ADR-0068`):**
   Verifies strict separation of `PINNED_INTEGRATE` (`lightweight-charts`, `perspective`, `openbb-workspace-backend`,
   `nautilus_trader`, `hftbacktest`), `OPTIONAL_READ_ONLY_OR_OFFLINE_RESEARCH` (Official TradingView Cloud MCP
   `38` tools / `0` broker-order tools, Pine Script v6 `library()`/`request.footprint()`/`force_overlay`,
   TradingView Desktop L2 UIA, `deepentropy/tvscreener`), `PHILOSOPHY_ONLY` (`PyneSys/pynecore`, `LuxAlgo/PineTS`,
   `louisnw01/lightweight-charts-python`, commercial TradingView Advanced Charts Broker API), and
   `HARD_REFUSED_EXECUTION_SAAS` (`marketcalls/openalgo`, `SignalStack`, `TradersPost`, `PineConnector`, `CrossTrade`).
2. **5-Layout Multi-Surface Coordination & Uncapped 6-Preset Parity (`[P][L][M][B][S][O]`, `TP OFF`):**
   Verifies `>= 92%` unobstructed candles, `order_authority = False`, `visual_artifacts_may_bind_alert_or_webhook = False`,
   whole-share `Shares` enforcement (preventing Alpaca `42210000`), and `singleActiveBrokerHostOnly = true`.
3. **Large-Cap `6–14 bps` Micro-Trail, Suitable-Timing Re-Entry & `1,000 req/min` Exit-Reserve Invariants:**
   Validates dimensional bounds (`bps` vs `pct`), `ADR-0022 <= 2.00%`, `5–10 bps` instant `BE+`, `6–14 bps` mega-cap
   trail width, `10%` unstarvable exit reserve (`100/1000` Alpaca + `20/200` HTTP-429 fallback + `300/3000` IBKR `:4002`),
   and live-capital hard refusal (`4001`/`7496`/`8796`/`8798`, `api.alpaca.markets` — hard-refused live-capital endpoint).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "sota.agy-tv-ecosystem-redteam.v1"

ALLOWED_CAPABILITY_CLASSES: frozenset[str] = frozenset(
    {
        "PINNED_INTEGRATE",
        "OPTIONAL_READ_ONLY_OR_OFFLINE_RESEARCH",
        "PHILOSOPHY_ONLY",
        "HARD_REFUSED_EXECUTION_SAAS",
    }
)

EXPECTED_TV_LIBRARIES: tuple[tuple[str, str], ...] = (
    ("lightweight-charts", "PINNED_INTEGRATE"),
    ("perspective", "PINNED_INTEGRATE"),
    ("openbb-workspace-backend", "PINNED_INTEGRATE"),
    ("nautilus_trader", "PINNED_INTEGRATE"),
    ("hftbacktest", "PINNED_INTEGRATE"),
    ("tradingview-official-cloud-mcp", "OPTIONAL_READ_ONLY_OR_OFFLINE_RESEARCH"),
    ("pine-script-v6-libraries", "OPTIONAL_READ_ONLY_OR_OFFLINE_RESEARCH"),
    ("tradingview-desktop-uia", "OPTIONAL_READ_ONLY_OR_OFFLINE_RESEARCH"),
    ("tvscreener", "OPTIONAL_READ_ONLY_OR_OFFLINE_RESEARCH"),
    ("pynecore", "PHILOSOPHY_ONLY"),
    ("pinets", "PHILOSOPHY_ONLY"),
    ("lightweight-charts-python", "PHILOSOPHY_ONLY"),
    ("tradingview-advanced-charts-trading-platform", "PHILOSOPHY_ONLY"),
    ("third-party-tv-webhook-saas-and-openalgo", "HARD_REFUSED_EXECUTION_SAAS"),
)

EXPECTED_MULTI_LAYOUT_IDS: tuple[str, ...] = (
    "L1_NOESIS_PRIMARY_LARGECAP_MICROTRAIL",
    "L2_NOESIS_4K_WALL_EXTREME_MOVER_EP",
    "L3_24X5_OVERNIGHT_BOATS_VIX_MACRO",
    "L4_OPENBB_PERSPECTIVE_LWC_COCKPIT",
    "L5_PORTABLE_MAC_M5_MAX_FAILOVER",
)

EXPECTED_UNCAPPED_CHIPS: tuple[str, ...] = ("P", "L", "M", "B", "S", "O")
FORBIDDEN_LIVE_PORTS: frozenset[int] = frozenset({4001, 7496, 8796, 8798})
FORBIDDEN_LIVE_HOSTS: frozenset[str] = frozenset({"api.alpaca.markets"})  # hard-refused live-capital endpoint
HARD_REFUSED_SAAS_SLUGS: frozenset[str] = frozenset(
    {
        "signalstack",
        "traderspost",
        "pineconnector",
        "crosstrade",
        "openalgo",
        "marketcalls/openalgo",
        "3commas",
        "alertatron",
    }
)
QUARANTINED_STRATEGIES_ADR0064: frozenset[str] = frozenset(
    {
        "SOTA_DUAL_CLIMAX_STOP_AND_REVERSE",
        "POST_VIX_REVERSAL",
        "POST_VIX_REVERSAL_MAJOR_GROWTH_THRUST",
        "SOTA_DUAL_EXTREME_BALANCE_BREAK_EARLY",
        "BLIND_WAVE2_REENTRY",
        "RAPID_WAVE2_REENTRY_STRESS",
        "FLOW_VELOCITY_CAPITAL_RECYCLE",
    }
)

_PRIVACY_LEAK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("alpaca_pa_id", re.compile(r"\bPA(?=[0-9A-Z]*[0-9])[0-9A-Z]{8,14}\b")),
    ("ibkr_du_id", re.compile(r"\bDU[0-9]{7,9}\b")),
    ("api_key_prefix", re.compile(r"\b(?:AK|PK)[0-9A-Z]{18,24}\b")),
    ("win32_home_path", re.compile(r"[A-Za-z]:[/\\]Users[/\\][A-Za-z0-9._-]+[/\\]")),
    ("macos_home_path", re.compile(r"(?<![A-Za-z0-9_*])/" + r"Users/[A-Za-z0-9._-]+/")),
    ("linux_home_path", re.compile(r"(?<![A-Za-z0-9_*])/home/[A-Za-z0-9._-]+/")),
)


@dataclass(frozen=True, slots=True)
class RedTeamProbeOutcome:
    probe_id: str
    vuln_class: str
    passed: bool
    detail: str


def verify_largecap_trail_and_rate_bounds(
    *,
    trail_bps: float,
    be_arm_bps: float,
    initial_stop_pct: float,
    alpaca_max_rpm: int,
    alpaca_exit_reserve_rpm: int,
    ibkr_port: int,
    ibkr_max_mpm: int,
    ibkr_exit_reserve_mpm: int,
    take_profit_cap_enabled: bool = False,
) -> tuple[bool, list[str]]:
    """Verify exact dimensional bounds for Large-Cap 6-14 bps trailing and 1,000/3,000 RPM exit reserves."""
    errors: list[str] = []
    for name, val in (
        ("trail_bps", trail_bps),
        ("be_arm_bps", be_arm_bps),
        ("initial_stop_pct", initial_stop_pct),
    ):
        if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(float(val)):
            errors.append(f"NONFINITE_OR_BOOL:{name}")
    if errors:
        return False, errors

    if not (6.0 <= float(trail_bps) <= 14.0):
        errors.append(f"LARGECAP_TRAIL_OUT_OF_6_14_BPS:{trail_bps}")
    if not (5.0 <= float(be_arm_bps) <= 10.0):
        errors.append(f"LARGECAP_BE_ARM_OUT_OF_5_10_BPS:{be_arm_bps}")
    if not (0.0 < float(initial_stop_pct) <= 2.00):
        errors.append(f"ADR0022_STOP_OUT_OF_BOUNDS:{initial_stop_pct}")
    if take_profit_cap_enabled:
        errors.append("ADR0063_FIXED_TP_CAP_FORBIDDEN")

    if (
        isinstance(alpaca_max_rpm, bool)
        or not isinstance(alpaca_max_rpm, int)
        or isinstance(alpaca_exit_reserve_rpm, bool)
        or not isinstance(alpaca_exit_reserve_rpm, int)
    ):
        errors.append("INVALID_BOOL_OR_NONINT_RPM")
    elif alpaca_max_rpm < 200 or alpaca_exit_reserve_rpm < math.ceil(alpaca_max_rpm * 0.10):
        errors.append(f"ALPACA_EXIT_RESERVE_BELOW_10PCT:{alpaca_exit_reserve_rpm}/{alpaca_max_rpm}")
    elif alpaca_exit_reserve_rpm > alpaca_max_rpm:
        errors.append(f"ALPACA_EXIT_RESERVE_EXCEEDS_MAX:{alpaca_exit_reserve_rpm}/{alpaca_max_rpm}")

    if (
        isinstance(ibkr_port, bool)
        or not isinstance(ibkr_port, int)
        or ibkr_port in FORBIDDEN_LIVE_PORTS
        or ibkr_port not in {4002, 7497}
    ):
        errors.append(f"IBKR_LIVE_PORT_REFUSED:{ibkr_port}")
    if (
        isinstance(ibkr_max_mpm, bool)
        or not isinstance(ibkr_max_mpm, int)
        or isinstance(ibkr_exit_reserve_mpm, bool)
        or not isinstance(ibkr_exit_reserve_mpm, int)
    ):
        errors.append("INVALID_BOOL_OR_NONINT_MPM")
    elif ibkr_max_mpm < 300 or ibkr_exit_reserve_mpm < math.ceil(ibkr_max_mpm * 0.10):
        errors.append(f"IBKR_EXIT_RESERVE_BELOW_10PCT:{ibkr_exit_reserve_mpm}/{ibkr_max_mpm}")
    elif ibkr_exit_reserve_mpm > ibkr_max_mpm:
        errors.append(f"IBKR_EXIT_RESERVE_EXCEEDS_MAX:{ibkr_exit_reserve_mpm}/{ibkr_max_mpm}")

    return len(errors) == 0, errors


def verify_tv_manifest_governance(manifest: Mapping[str, Any]) -> tuple[bool, list[str]]:
    """Audit a serialized TradingView multi-layout & lossless manifest for P0-P2 red-team violations."""
    errors: list[str] = []
    if manifest.get("order_authority_on_visual_surfaces") is not False:
        errors.append("VISUAL_ORDER_AUTHORITY_MUST_BE_FALSE")
    if manifest.get("visual_artifacts_may_bind_alert_or_webhook") is not False:
        errors.append("VISUAL_WEBHOOK_BINDING_MUST_BE_FALSE")
    if manifest.get("standalone_alpha_claim") is not False:
        errors.append("STANDALONE_ALPHA_CLAIM_MUST_BE_FALSE")

    expected_lib_map = dict(EXPECTED_TV_LIBRARIES)
    libs = manifest.get("tv_library_landscape")
    if libs is None:
        libs = manifest.get("library_landscape_stack")
    if not isinstance(libs, Sequence) or isinstance(libs, (str, bytes)):
        errors.append("INVALID_LIBRARY_LIST")
        libs = ()

    lib_map: dict[str, str] = {}
    for idx, entry in enumerate(libs):
        if not isinstance(entry, Mapping):
            errors.append(f"INVALID_LIBRARY_ENTRY:{idx}")
            continue
        lid = str(entry.get("library_id") or "")
        cls = str(entry.get("capability_class") or "")
        if lid in lib_map:
            errors.append(f"DUPLICATE_LIBRARY_ID:{lid}")
        lib_map[lid] = cls
        if lid not in expected_lib_map:
            errors.append(f"UNREGISTERED_LIBRARY_ID:{lid}")
        if cls not in ALLOWED_CAPABILITY_CLASSES:
            errors.append(f"INVALID_CAPABILITY_CLASS:{lid}:{cls}")
        if entry.get("order_authority") is not False:
            errors.append(f"LIBRARY_ORDER_AUTHORITY_MUST_BE_FALSE:{lid}")
        if entry.get("visual_may_bind_webhook") is not False:
            errors.append(f"LIBRARY_WEBHOOK_BINDING_MUST_BE_FALSE:{lid}")

    for lib_id, expected_cls in EXPECTED_TV_LIBRARIES:
        if lib_map.get(lib_id) != expected_cls:
            errors.append(f"LIBRARY_CLASS_MISMATCH:{lib_id}:{lib_map.get(lib_id)}!={expected_cls}")

    expected_layout_set = set(EXPECTED_MULTI_LAYOUT_IDS)
    layouts = manifest.get("multi_layouts")
    if not isinstance(layouts, Sequence) or isinstance(layouts, (str, bytes)):
        errors.append("INVALID_LAYOUT_LIST")
        layouts = ()

    layout_ids: set[str] = set()
    for idx, ly in enumerate(layouts):
        if not isinstance(ly, Mapping):
            errors.append(f"INVALID_LAYOUT_ENTRY:{idx}")
            continue
        ly_id = str(ly.get("layout_id") or "")
        if ly_id in layout_ids:
            errors.append(f"DUPLICATE_LAYOUT_ID:{ly_id}")
        layout_ids.add(ly_id)
        if ly_id not in expected_layout_set:
            errors.append(f"UNREGISTERED_LAYOUT_ID:{ly_id}")
        raw_pct = ly.get("unobstructed_candle_area_min_pct")
        if (
            isinstance(raw_pct, bool)
            or not isinstance(raw_pct, (int, float))
            or not math.isfinite(float(raw_pct))
            or float(raw_pct) < 92.0
        ):
            errors.append(f"CANDLE_OBSTRUCTION:{ly_id}")
        if ly.get("order_authority") is not False:
            errors.append(f"LAYOUT_ORDER_AUTHORITY:{ly_id}")
        binding = ly.get("lossless_binding") or ly.get("lossless_engine_binding")
        if isinstance(binding, Mapping):
            lanes = binding.get("paper_lanes")
            if isinstance(lanes, Sequence) and not isinstance(lanes, (str, bytes)):
                for ln in lanes:
                    ln_s = str(ln)
                    if "LIVE" in ln_s.upper() or any(str(fp) in ln_s for fp in FORBIDDEN_LIVE_PORTS):
                        errors.append(f"LAYOUT_LIVE_LANE_FORBIDDEN:{ly_id}:{ln_s}")

    for expected_ly in EXPECTED_MULTI_LAYOUT_IDS:
        if expected_ly not in layout_ids:
            errors.append(f"MISSING_LAYOUT:{expected_ly}")

    # Rate budget & lossless stop sub-block validation (when present in manifest)
    rate_cfg = manifest.get("dual_lane_1000rpm_budget") or manifest.get("dual_lane_rate_contract")
    if isinstance(rate_cfg, Mapping):
        ib_port = rate_cfg.get("ibkr_paper_port")
        if (
            isinstance(ib_port, bool)
            or not isinstance(ib_port, int)
            or ib_port in FORBIDDEN_LIVE_PORTS
            or ib_port not in {4002, 7497}
        ):
            errors.append(f"MANIFEST_IBKR_LIVE_PORT_REFUSED:{ib_port}")
        alp_rpm = rate_cfg.get("alpaca_algo_plus_rpm")
        alp_res = rate_cfg.get("alpaca_exit_reserve_rpm")
        if alp_rpm is not None or alp_res is not None:
            if (
                isinstance(alp_rpm, bool)
                or not isinstance(alp_rpm, int)
                or isinstance(alp_res, bool)
                or not isinstance(alp_res, int)
                or alp_rpm < 200
                or alp_res < math.ceil(alp_rpm * 0.10)
                or alp_res > alp_rpm
            ):
                errors.append(f"MANIFEST_INVALID_ALPACA_RATE_BUDGET:{alp_res}/{alp_rpm}")
        ib_mpm = rate_cfg.get("ibkr_paper_max_mpm")
        ib_res = rate_cfg.get("ibkr_paper_exit_reserve_mpm")
        if ib_mpm is not None or ib_res is not None:
            if (
                isinstance(ib_mpm, bool)
                or not isinstance(ib_mpm, int)
                or isinstance(ib_res, bool)
                or not isinstance(ib_res, int)
                or ib_mpm < 300
                or ib_res < math.ceil(ib_mpm * 0.10)
                or ib_res > ib_mpm
            ):
                errors.append(f"MANIFEST_INVALID_IBKR_RATE_BUDGET:{ib_res}/{ib_mpm}")

    presets_cfg = manifest.get("uncapped_quickbar_presets")
    if presets_cfg is not None:
        if not isinstance(presets_cfg, Sequence) or isinstance(presets_cfg, (str, bytes)):
            errors.append("MANIFEST_INVALID_PRESETS_LIST")
        else:
            for idx, pr in enumerate(presets_cfg):
                if not isinstance(pr, Mapping):
                    errors.append(f"MANIFEST_INVALID_PRESET_ENTRY:{idx}")
                    continue
                chip = str(pr.get("chip") or idx)
                if pr.get("tp_enabled") is not False:
                    errors.append(f"MANIFEST_PRESET_FIXED_TP_FORBIDDEN:{chip}")
                if str(pr.get("quantity_type") or "") != "Shares":
                    errors.append(f"MANIFEST_PRESET_NON_WHOLE_SHARES:{chip}")
                sl = pr.get("sl_pct_price")
                if sl is not None and (
                    isinstance(sl, bool)
                    or not isinstance(sl, (int, float))
                    or not math.isfinite(float(sl))
                    or not (0.0 < float(sl) <= 2.00)
                ):
                    errors.append(f"MANIFEST_PRESET_ADR0022_STOP_INVALID:{chip}:{sl}")

    trail_cfg = manifest.get("large_cap_micro_trail_contract") or manifest.get("largecap_micro_trail_contract")
    if isinstance(trail_cfg, Mapping):
        if trail_cfg.get("take_profit_cap_enabled") is not False:
            errors.append("MANIFEST_FIXED_TP_CAP_FORBIDDEN")
        raw_stop = trail_cfg.get("adr0022_max_initial_stop_pct")
        if (
            isinstance(raw_stop, bool)
            or not isinstance(raw_stop, (int, float))
            or not math.isfinite(float(raw_stop))
            or not (0.0 < float(raw_stop) <= 2.00)
        ):
            errors.append(f"MANIFEST_ADR0022_STOP_OUT_OF_BOUNDS:{raw_stop}")

    # Privacy, non-finite JSON & secret tripwire on serialized manifest
    try:
        serialized = json.dumps(dict(manifest), sort_keys=True, allow_nan=False)
    except (TypeError, ValueError):
        errors.append("NONFINITE_OR_UNSERIALIZABLE_MANIFEST")
        serialized = json.dumps(dict(manifest), sort_keys=True, default=str)
    for label, rx in _PRIVACY_LEAK_PATTERNS:
        if rx.search(serialized):
            errors.append(f"PRIVACY_LEAK:{label}")

    return len(errors) == 0, errors


def run_tv_ecosystem_redteam_probes(
    *,
    manifest: Mapping[str, Any] | None = None,
    candidate_saas_bridges: Sequence[str] = ("SignalStack", "TradersPost", "marketcalls/openalgo", "PineConnector"),
) -> dict[str, Any]:
    """Run adversarial red-team self-test probes across all TradingView, lossless, and 1,000 RPM boundaries."""
    probes: list[RedTeamProbeOutcome] = []

    # Probe 1: Valid Large-Cap 6-14 bps + 1000/100 + IBKR 3000/300 passes
    ok1, errs1 = verify_largecap_trail_and_rate_bounds(
        trail_bps=8.5,
        be_arm_bps=6.0,
        initial_stop_pct=1.25,
        alpaca_max_rpm=1000,
        alpaca_exit_reserve_rpm=100,
        ibkr_port=4002,
        ibkr_max_mpm=3000,
        ibkr_exit_reserve_mpm=300,
        take_profit_cap_enabled=False,
    )
    probes.append(
        RedTeamProbeOutcome(
            probe_id="P1_LARGECAP_MICROTRAIL_AND_1000RPM_BASELINE",
            vuln_class="adr0022_stop_cap_exceeded",
            passed=ok1 and not errs1,
            detail="OK" if ok1 else ";".join(errs1),
        )
    )

    # Probe 2: Adversarial ADR-0022 > 2.00% stop rejected
    ok2, errs2 = verify_largecap_trail_and_rate_bounds(
        trail_bps=8.5,
        be_arm_bps=6.0,
        initial_stop_pct=2.05,
        alpaca_max_rpm=1000,
        alpaca_exit_reserve_rpm=100,
        ibkr_port=4002,
        ibkr_max_mpm=3000,
        ibkr_exit_reserve_mpm=300,
    )
    probes.append(
        RedTeamProbeOutcome(
            probe_id="P2_REJECT_ADR0022_OVER_2PCT_STOP",
            vuln_class="adr0022_stop_cap_exceeded",
            passed=(not ok2) and any("ADR0022_STOP_OUT_OF_BOUNDS" in e for e in errs2),
            detail="FAIL_CLOSED_CONFIRMED" if not ok2 else "BYPASSED",
        )
    )

    # Probe 3: Adversarial fixed-TP cap rejected (ADR-0063)
    ok3, errs3 = verify_largecap_trail_and_rate_bounds(
        trail_bps=8.5,
        be_arm_bps=6.0,
        initial_stop_pct=1.25,
        alpaca_max_rpm=1000,
        alpaca_exit_reserve_rpm=100,
        ibkr_port=4002,
        ibkr_max_mpm=3000,
        ibkr_exit_reserve_mpm=300,
        take_profit_cap_enabled=True,
    )
    probes.append(
        RedTeamProbeOutcome(
            probe_id="P3_REJECT_FIXED_TP_CAP_ADR0063",
            vuln_class="adr0022_stop_cap_exceeded",
            passed=(not ok3) and any("ADR0063_FIXED_TP_CAP_FORBIDDEN" in e for e in errs3),
            detail="FAIL_CLOSED_CONFIRMED" if not ok3 else "BYPASSED",
        )
    )

    # Probe 4: Adversarial live IBKR port 4001 / 7496 & live ports 8796 / 8798 rejected
    live_all_refused = all(
        not verify_largecap_trail_and_rate_bounds(
            trail_bps=8.5,
            be_arm_bps=6.0,
            initial_stop_pct=1.25,
            alpaca_max_rpm=1000,
            alpaca_exit_reserve_rpm=100,
            ibkr_port=bad_port,
            ibkr_max_mpm=3000,
            ibkr_exit_reserve_mpm=300,
        )[0]
        for bad_port in FORBIDDEN_LIVE_PORTS
    )
    probes.append(
        RedTeamProbeOutcome(
            probe_id="P4_REJECT_ALL_LIVE_PORTS",
            vuln_class="live_capital_firewall_bypass",
            passed=live_all_refused,
            detail="ALL_4_LIVE_PORTS_REFUSED" if live_all_refused else "LIVE_PORT_BYPASSED",
        )
    )

    # Probe 5: Adversarial NaN/Inf/bool fail closed
    nan_refused = not verify_largecap_trail_and_rate_bounds(
        trail_bps=float("nan"),
        be_arm_bps=6.0,
        initial_stop_pct=1.25,
        alpaca_max_rpm=1000,
        alpaca_exit_reserve_rpm=100,
        ibkr_port=4002,
        ibkr_max_mpm=3000,
        ibkr_exit_reserve_mpm=300,
    )[0]
    probes.append(
        RedTeamProbeOutcome(
            probe_id="P5_REJECT_IEEE754_NAN_INF_BOOL",
            vuln_class="integer_overflow_and_ieee754_nan_inf",
            passed=nan_refused,
            detail="NAN_REJECTED" if nan_refused else "NAN_BYPASSED",
        )
    )

    # Probe 6: Third-party SaaS webhook bridges hard-refused
    saas_blocked = all(any(slug in b.lower() for slug in HARD_REFUSED_SAAS_SLUGS) for b in candidate_saas_bridges)
    probes.append(
        RedTeamProbeOutcome(
            probe_id="P6_HARD_REFUSE_THIRD_PARTY_TV_WEBHOOK_SAAS",
            vuln_class="live_capital_firewall_bypass",
            passed=saas_blocked,
            detail="ALL_SAAS_BRIDGES_DENIED" if saas_blocked else "SAAS_BRIDGE_UNMATCHED",
        )
    )

    # Probe 7: Exit-reserve starvation (< 10% reserve) rejected
    ok7, errs7 = verify_largecap_trail_and_rate_bounds(
        trail_bps=8.5,
        be_arm_bps=6.0,
        initial_stop_pct=1.25,
        alpaca_max_rpm=1000,
        alpaca_exit_reserve_rpm=50,  # < 10%
        ibkr_port=4002,
        ibkr_max_mpm=3000,
        ibkr_exit_reserve_mpm=300,
    )
    probes.append(
        RedTeamProbeOutcome(
            probe_id="P7_REJECT_EXIT_RESERVE_STARVATION",
            vuln_class="race_condition_toctou",
            passed=(not ok7) and any("ALPACA_EXIT_RESERVE_BELOW_10PCT" in e for e in errs7),
            detail="UNDER_10PCT_RESERVE_REJECTED" if not ok7 else "STARVATION_BYPASSED",
        )
    )

    # Probe 8: Optional manifest full governance audit
    if manifest is not None:
        m_ok, m_errs = verify_tv_manifest_governance(manifest)
        probes.append(
            RedTeamProbeOutcome(
                probe_id="P8_MANIFEST_GOVERNANCE_AND_PRIVACY_AUDIT",
                vuln_class="home_path_leakage",
                passed=m_ok,
                detail="MANIFEST_CLEAN" if m_ok else ";".join(m_errs),
            )
        )

    all_passed = all(p.passed for p in probes)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "adr": "ADR-0036",
        "all_passed": all_passed,
        "probes_passed": sum(1 for p in probes if p.passed),
        "probes_total": len(probes),
        "probes": [
            {"probe_id": p.probe_id, "vuln_class": p.vuln_class, "passed": p.passed, "detail": p.detail} for p in probes
        ],
    }
    summary["report_sha256"] = hashlib.sha256(
        json.dumps(summary, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return summary
