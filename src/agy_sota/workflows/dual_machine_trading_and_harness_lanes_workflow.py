# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA Schema-Typed `run_workflow`: Dual-Machine (`Mac M5 Max <-> Noesis`) Trading & Harness Lanes Audit.

Verifies `ADR-0020` (`v3.7.0`) across Portable Apple M5 Max (`macOS`) and Stationary `Noesis`
(`Windows` + `WSL2 Noesis-Carbon`) over symmetric Tailscale Orca (`:6770`):
- Trading Lanes `T1..T3` (Sim/Pre-Wall/Shelf Lock, Paper Execution Split-Brain Firewall `:8787`/`:4002`,
  and `24/5` Guardian/Compounding/Vault `:8799`).
- Harness Lanes `H1..H3` (`cc-lead` Central Hub, `AGY` + `MMW` DAGs, and `DSH`/`Codex`/`OMO`/`Orca` Fleet)
  across all `8` Multi-Model Orchestration Frameworks and `>= 11` `orca.yaml` workspace recipes.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

cfg = args if "args" in globals() and isinstance(args, dict) else {}
target_repo = str(cfg.get("repo") or "agy-sota-harness")
rc_ctx = getattr(kit, "load_research_convergence_context", lambda: {"schema_version": "sota-research-feeds.v2"})()
rc_envelope = getattr(kit, "verify_workflow_research_convergence", lambda *_a, **_k: {"valid": True})(
    "dual-machine-trading-and-harness-lanes", repo=target_repo
)
rc_schema = str(rc_ctx.get("schema_version") or "sota-research-feeds.v2")
peer_brief = kit.load_peer_brief(target_repo)
log(f"{peer_brief}\n[RC Envelope valid={rc_envelope.get('valid', True)} | schema={rc_schema}]")

LANE_AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "lane_group": {"type": "string"},
        "lanes_verified": {"type": "array", "items": {"type": "string"}},
        "orca_yaml_count": {"type": "integer"},
        "split_brain_safe": {"type": "boolean"},
        "findings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["lane_group", "lanes_verified", "orca_yaml_count", "split_brain_safe", "findings"],
}

CONVERGENCE_VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "converged": {"type": "boolean"},
        "evidence_grade": {"type": "string", "enum": ["E0", "E1", "E2", "E3", "E4"]},
        "trading_lanes_healthy": {"type": "boolean"},
        "harness_lanes_healthy": {"type": "boolean"},
        "orchestration_frameworks_count": {"type": "integer"},
        "executive_summary": {"type": "string"},
        "next_action": {"type": "string"},
    },
    "required": [
        "converged",
        "evidence_grade",
        "trading_lanes_healthy",
        "harness_lanes_healthy",
        "orchestration_frameworks_count",
        "executive_summary",
        "next_action",
    ],
}

LANE_SWEEPS = [
    (
        "Trading Lanes T1-T3 Auditor",
        "research",
        f"{peer_brief}\n\n"
        f"Enforce `{rc_schema}` PIT contract & ADR-0004/ADR-0016/ADR-0020 3-tier SHA provenance "
        "(other_repos_authority == PHILOSOPHY_ONLY; pre-wall <= 2026-10-15; ADR-0022 <= 2.00% stop).\n"
        "Read-only audit of Dual-Machine (`Mac M5 Max <-> Noesis`) Trading Lanes:\n"
        "- T1 Sim, Pre-Wall Research & 18-Clone Shelf Lock (`meridian`, `sota-compounding-lab`, `sota-upstream-shelf-lock`)\n"
        "- T2 Paper Execution Split-Brain Firewall (`sota-mover-ranker` :8787 <=200/min Alpaca Paper, `astrolabe` :4002 <=3,000/min IBKR Paper; never restart live :8787)\n"
        "- T3 24/5 Dynamic Trail Guardian & Vault (`sota-dynamic-trail-c` :8799, `sota-private-vault`; never restart live :8799)\n"
        "Verify `orca.yaml` presence and zero secret/account-ID leaks.",
    ),
    (
        "Harness Lanes H1-H3 & 8-Framework Auditor",
        "research",
        f"{peer_brief}\n\n"
        f"Enforce `{rc_schema}` PIT contract & ADR-0004/ADR-0016/ADR-0020 3-tier SHA provenance "
        "(other_repos_authority == PHILOSOPHY_ONLY).\n"
        "Read-only audit of Dual-Machine (`Mac M5 Max <-> Noesis`) Harness Lanes & 8 Orchestration Frameworks:\n"
        "- H1 Central `cc-lead` (`OMC` v2) & Open-Core Foundation (`cc-sota-harness`, `sota-harness-foundation`, `native-agent-stack`)\n"
        "- H2 Antigravity `L0-L12` (`agy-sota-harness`, 6 local `run_workflow` DAGs + Native Swarm) & `sota-multi-model-workflows` (14 `REGISTRY.json` DAGs)\n"
        "- H3 Multi-Runtime Worker Fleet (`dsh-sota-harness`, `dsh-plugin-landscape`, `Codex OMX`, `OpenCode OMO`, `Composio AO`, `Orca` `:6770`, `hcom`, `sota-peer-bus`)\n"
        "Verify >=11 `orca.yaml` workspace recipes across `~/Documents/*` and `~/.agents/bin/sota-doctor`.",
    ),
]

phase("1. Parallel Dual-Machine Trading Lanes (T1-T3) & Harness Lanes (H1-H3) Reconnaissance")

lane_audits = await parallel(
    LANE_SWEEPS,
    lambda item: agent(item[2], schema=LANE_AUDIT_SCHEMA, role=item[0], type_name=item[1], model="flash"),
)

phase("2. Deterministic Dual-Machine Orca Lane & 8-Framework Convergence Verdict")

verdict = await agent(
    f"{peer_brief}\n\n"
    f"Enforce `{rc_schema}` & ADR-0020 (`other_repos_authority == PHILOSOPHY_ONLY`).\n"
    f"Synthesize Trading Lanes (`T1..T3`) and Harness Lanes (`H1..H3`) audit results:\n{json.dumps(lane_audits)}\n"
    "Confirm all 8 orchestration frameworks (AGY `run_workflow`/Swarm, Claude `OMC` v2, Codex `OMX`, "
    "`Orca` `:6770`, OpenCode `OMO`, DeepSeek `DSH`, Composio `AO`, `sota-peer-bus`+`hcom`) and >=11 `orca.yaml` "
    "recipes are converged with single-active-broker-host safety.",
    schema=CONVERGENCE_VERDICT_SCHEMA,
    role="Dual-Machine Lane Convergence Verifier",
    type_name="sota-code-verifier",
)

kit.record_workflow_run(
    repo=target_repo,
    workflow_id="dual-machine-trading-and-harness-lanes",
    done_summary=(
        f"converged={verdict['converged']} (grade={verdict['evidence_grade']}, "
        f"frameworks={verdict['orchestration_frameworks_count']}): {verdict['executive_summary'][:300]}"
    ),
    verified_by=f"T1-T3={verdict['trading_lanes_healthy']}; H1-H3={verdict['harness_lanes_healthy']}",
    open_risks="; ".join((lane_audits[0]["findings"] + lane_audits[1]["findings"])[:3]) or "none",
    next_priority=verdict["next_action"],
)

out_payload = json.dumps({"lane_audits": lane_audits, "verdict": verdict}, indent=2)
log(out_payload)
print(out_payload)
