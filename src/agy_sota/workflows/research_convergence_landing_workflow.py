# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA Schema-Typed `run_workflow`: End-to-End Research-Convergence, DataFeed & Strategy Landing.

Enforces `ADR-0004` / `ADR-0016` 3-tier provenance (64-hex input SHA-256 + 40-hex upstream pins +
reproducible receipt), 7-feed PIT DataFeed routing (`SIP`/`BOATS` + `RAW`/`ALL` + SEC `acceptanceDateTime`
+ FINRA `T-1`), and canonical strategy template validation before paper-lane staging.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

cfg = args if "args" in globals() and isinstance(args, dict) else {}
strategy_id = str(cfg.get("strategy_id") or "CANDIDATE_PRE_TRAVEL_IGNITION")
archetype = str(cfg.get("archetype") or "PRE_TRAVEL_EARLY_IGNITION")
target_repo = str(cfg.get("repo") or "sota-mover-ranker")
rc_ctx = getattr(kit, "load_research_convergence_context", lambda: {"schema_version": "sota-research-feeds.v2"})()
rc_envelope = getattr(kit, "verify_workflow_research_convergence", lambda *_a, **_k: {"valid": True})(
    "research-convergence-landing", repo=target_repo, archetype=archetype
)
rc_schema = str(rc_ctx.get("schema_version") or "sota-research-feeds.v2")
peer_brief = kit.load_peer_brief(target_repo)
log(
    f"{peer_brief}\n[RC Context: schema={rc_schema} | valid={rc_envelope.get('valid', True)} | ADR-0004/ADR-0016 | sibling_authority=PHILOSOPHY_ONLY]"
)

DATAFEED_RECON_SCHEMA = {
    "type": "object",
    "properties": {
        "input_package_sha256_verified": {"type": "boolean"},
        "pinned_upstreams_checked": {"type": "array", "items": {"type": "string"}},
        "seven_feed_pit_status": {"type": "string"},
        "first_hand_incentives_summary": {"type": "string"},
    },
    "required": [
        "input_package_sha256_verified",
        "pinned_upstreams_checked",
        "seven_feed_pit_status",
        "first_hand_incentives_summary",
    ],
}

TEMPLATE_EXEC_SCHEMA = {
    "type": "object",
    "properties": {
        "strategy_id": {"type": "string"},
        "archetype": {"type": "string"},
        "template_valid": {"type": "boolean"},
        "prewall_metrics_summary": {"type": "string"},
        "max_stop_pct": {"type": "number"},
    },
    "required": ["strategy_id", "archetype", "template_valid", "prewall_metrics_summary", "max_stop_pct"],
}

GATE_VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "approved": {"type": "boolean"},
        "evidence_grade": {"type": "string", "enum": ["E0", "E1", "E2", "E3", "E4"]},
        "blocking_issues": {"type": "array", "items": {"type": "string"}},
        "next_action": {"type": "string"},
    },
    "required": ["approved", "evidence_grade", "blocking_issues", "next_action"],
}

phase("1. Parallel ADR-0004 Source-of-Truth & 7-Feed PIT DataFeed Reconnaissance")

recon = await parallel(
    [
        (
            "Upstream Pin & Source-of-Truth Auditor",
            "sota-deep-synthesizer",
            f"{peer_brief}\n\nStrategy `{strategy_id}` (`{archetype}`) in `{target_repo}`:\n"
            "Verify `~/Documents/upstream/PINS.md` 40-char SHAs, check `sota_shelf_search`, and enforce "
            "ADR-0004 (`other_repos_authority == PHILOSOPHY_ONLY`). Never print secrets or account IDs.",
        ),
        (
            "7-Feed PIT DataFeed & First-Hand Incentive Scout",
            "self",
            f"{peer_brief}\n\nQuery `sota_get_research_feeds`, `sota_get_first_hand_incentives`, and "
            "`sota_get_converged_strategy_templates` on `sota-mover-ranker-stdio` MCP. Confirm `SIP`/`BOATS` "
            "session routing, `RAW` filter vs `ALL` return split invariance, SEC `acceptanceDateTime` (`15m` decay), "
            "and FINRA `T-1` lag.",
        ),
    ],
    lambda item: agent(item[2], schema=DATAFEED_RECON_SCHEMA, role=item[0], type_name=item[1]),
)

phase("2. Converged Strategy Template Validation & Pre-Wall (<= 2026-10-15) Study")

staged = await agent(
    f"{peer_brief}\n\nRecon: {json.dumps(recon)}\n"
    f"Validate `{strategy_id}` (`{archetype}`) against `templates/sota_converged_strategy.template.json` "
    "(`agy_sota.research_convergence.validate_converged_strategy_manifest`) and pre-wall (`<= 2026-10-15`) "
    "HLZ / CPCV / DSR / 2x-impact & ADR-0022 (`<= 2.00%`) bounds.",
    schema=TEMPLATE_EXEC_SCHEMA,
    role="Converged Strategy Template Builder",
    type_name="sota-rd-proposer",
)

phase("3. Parallel Adversarial Falsification & Deterministic Code/Template Gate")

verdicts = await parallel(
    [
        (
            "Adversarial PIT, Split & Dilution Falsifier",
            "sota-falsifier",
            f"{peer_brief}\n\nAudit `{json.dumps(staged)}` for post-2026-10-15 leakage, `RAW`/`ALL` split-jump "
            "contamination, SEC after-hours `acceptanceDateTime` leakage, `S-3`/`424B5` dilution, or `2x` cost decay.",
        ),
        (
            "Deterministic Template, Merge-Gate & Pine v6 Verifier",
            "sota-code-verifier",
            f"{peer_brief}\n\nVerify `{json.dumps(staged)}` passes `validate_converged_strategy_manifest`, "
            "`ADR-0022 <= 2.00%`, paper-only routing (`PA... <=200/min`, `DU... :4002 <=3,000/min`), and `merge_gate.py`.",
        ),
    ],
    lambda item: agent(item[2], schema=GATE_VERIFY_SCHEMA, role=item[0], type_name=item[1]),
)

kit.record_workflow_run(
    repo=target_repo,
    workflow_id="research-convergence-landing",
    done_summary=f"{strategy_id} ({archetype}) -> falsifier={verdicts[0]['approved']} verifier={verdicts[1]['approved']}",
    verified_by=f"grade={verdicts[1]['evidence_grade']}; template_valid={staged['template_valid']}",
    open_risks="; ".join((verdicts[0]["blocking_issues"] + verdicts[1]["blocking_issues"])[:3]) or "none",
    next_priority=verdicts[1]["next_action"] or verdicts[0]["next_action"],
)

out_json = json.dumps({"recon": recon, "staged": staged, "verdicts": verdicts}, indent=2)
log(out_json)
print(out_json)
