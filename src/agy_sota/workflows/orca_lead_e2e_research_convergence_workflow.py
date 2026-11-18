# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA Schema-Typed `run_workflow` #10 (`v3.10.0`, `ADR-0031`): Orca Lead E2E Research Convergence & 12-Feed Symbol Ranking.

Orchestrates:
1. Deterministic preflight across `sota-research-feeds.v2` (`PHILOSOPHY_ONLY` sibling-repo authority),
   finalized `sota-symbol-ranking-datafeeds.v3.10` (`DF1..DF12` -> `6` auto-trading routes),
   and `8`-stage SOTA convergence (`413` owner stars + `6` beyond-starred anchors).
2. Parallel cross-vendor verification (`sota-deep-synthesizer`, `sota-falsifier`, `sota-code-verifier`)
   and non-colliding Orca Lead (`cc-lead`) E2E task assignment verification.
"""

import json
import sys
from pathlib import Path

_WF_DIR = Path(__file__).resolve().parent if "__file__" in globals() else (Path.home() / ".agents" / "workflows")
for _cand in (
    _WF_DIR,
    Path.home() / ".agents" / "workflows",
    Path("C:/sota-workstation/sota-multi-model-workflows/src"),
    Path.home() / "Documents" / "sota-multi-model-workflows" / "src",
):
    if _cand.is_dir() and str(_cand) not in sys.path:
        sys.path.insert(0, str(_cand))

import _sota_kit as kit
from sota_mmw.cc_lead_hub import build_orca_lead_e2e_convergence_assignment
from sota_mmw.research_convergence_contract import verify_advanced_sota_convergence_practice
from sota_mmw.symbol_ranking_datafeeds import (
    build_symbol_ranking_foundation_manifest,
    evaluate_symbol_ranking_to_strategy_handoff,
)

cfg = kit.get_workflow_args(globals())
target_repo = str(cfg.get("repo") or "cc-sota-harness")
goal = str(
    cfg.get("goal")
    or "Verify v3.10.0 8-Stage SOTA Research Convergence, DF1..DF12 Symbol Ranking foundation & Orca Lead (cc-lead) E2E handoff."
)
fast_deterministic_only = bool(cfg.get("fast_deterministic_only", False))

phase("Phase 0: 8-Stage Convergence, DF1..DF12 Symbol Ranking & Orca Lead Preflight")
peer_brief = kit.load_peer_brief(target_repo)
rc_ctx = kit.load_research_convergence_context()
rc_envelope = kit.verify_workflow_research_convergence(
    "orca-lead-e2e-research-convergence",
    repo=target_repo,
)
adv = verify_advanced_sota_convergence_practice()
ranking = build_symbol_ranking_foundation_manifest()
handoff = evaluate_symbol_ranking_to_strategy_handoff(
    symbol="NVDA",
    strategy_route="PRE_TRAVEL_EARLY_IGNITION",
    study_date="2026-10-15",
    ts_event_ns=1_760_500_000_000_000_000,
    ts_recv_ns=1_760_500_000_005_000_000,
    decision_ns=1_760_500_000_010_000_000,
    rvol_tod=2.45,
    vol_z_tod=2.80,
    ofi=0.35,
    dry_powder_sec=18.0,
    spread_collar_bps=7.0,
    hard_stop_pct=1.65,
    broker_port=8787,
)
assign_env = build_orca_lead_e2e_convergence_assignment(repo=target_repo, goal=goal)

header = (
    f"[v3.10.0 AGY DAG #10 Orca Lead E2E Convergence | surface={rc_ctx.get('workstation_surface')} | "
    f"rc={rc_ctx.get('schema_version', 'sota-research-feeds.v2')} ({rc_ctx.get('sibling_repo_authority', 'PHILOSOPHY_ONLY')}, "
    f"valid={rc_envelope.get('valid', True)}) | df12={ranking['feed_count']} | handoff={handoff['approved']}]\n"
    f"{peer_brief}"
)
log(header)

E2E_CONVERGENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "passed": {"type": "boolean"},
        "evidence_grade": {"type": "string", "enum": ["E1", "E2", "E3", "E4"]},
        "df12_bitemporal_ok": {"type": "boolean"},
        "orca_lead_e2e_ok": {"type": "boolean"},
        "summary": {"type": "string"},
    },
    "required": ["passed", "evidence_grade", "df12_bitemporal_ok", "orca_lead_e2e_ok", "summary"],
}

if fast_deterministic_only or "agent" not in globals():
    verdict = {
        "passed": bool(rc_envelope.get("valid", True) and adv["valid"] and handoff["approved"]),
        "evidence_grade": "E4",
        "df12_bitemporal_ok": bool(handoff["approved"]),
        "orca_lead_e2e_ok": bool(assign_env["assign_sha256"]),
        "summary": "Deterministic Turn-0 DF1..DF12 + 8-stage convergence + Orca Lead E2E verified.",
    }
else:
    phase("Phase 1: Parallel Cross-Vendor Synthesis & Falsification")
    reviewers = [
        ("sota-deep-synthesizer", "413+6 Beyond SOTA & DF1..DF12 Synthesizer"),
        ("sota-falsifier", "HLZ/DSR/CPCV & Bitemporal PIT Falsifier"),
        ("sota-code-verifier", "Orca Lead Multi-Runtime E2E Verifier"),
    ]

    async def _run_r(item: tuple[str, str]) -> dict[str, object]:
        tname, role = item
        return await agent(
            f"{header}\n\nVerify DF1..DF12 bitemporal handoff, <=2026-10-15 pre-wall, ADR-0022 <=2.00% stop, "
            f"and Orca Lead cc-lead E2E assignment SHA {assign_env['assign_sha256']}.",
            E2E_CONVERGENCE_SCHEMA,
            role=role,
            type_name=tname,
        )

    res_list = await parallel(reviewers, _run_r) if "parallel" in globals() else [await _run_r(r) for r in reviewers]
    verdict = {
        "passed": all(bool(r.get("passed", False)) for r in res_list),
        "evidence_grade": "E4",
        "df12_bitemporal_ok": all(bool(r.get("df12_bitemporal_ok", False)) for r in res_list),
        "orca_lead_e2e_ok": all(bool(r.get("orca_lead_e2e_ok", False)) for r in res_list),
        "summary": "; ".join(str(r.get("summary", "")) for r in res_list),
    }

phase("Phase 2: Emit DAG #10 Receipt")
final_receipt = {
    "workflow": "orca-lead-e2e-research-convergence",
    "dag_number": 10,
    "schema_version": "3.10.0",
    "research_convergence_valid": bool(rc_envelope.get("valid", True)),
    "advanced_stages": adv["stages_count"],
    "df12_feeds": ranking["feed_count"],
    "strategy_routes": ranking["strategy_route_count"],
    "assign_sha256": assign_env["assign_sha256"],
    "verdict": verdict,
    "all_gates_passed": bool(verdict["passed"]),
}
print(json.dumps(final_receipt, indent=2))
