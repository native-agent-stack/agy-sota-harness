# ruff: noqa: F704, F821, PLE1142
"""AGY SOTA Schema-Typed `run_workflow`: Cross-Peer Lease, Verification & Orca Second-Opinion Gate."""

GATE_SCHEMA = {
    "type": "object",
    "properties": {
        "gate_passed": {"type": "boolean"},
        "p0_p1_findings": {"type": "array", "items": {"type": "string"}},
        "verification_commands_run": {"type": "array", "items": {"type": "string"}},
        "handover_ready_summary": {"type": "string"},
    },
    "required": ["gate_passed", "p0_p1_findings", "verification_commands_run", "handover_ready_summary"],
}

phase("Two-Pass Deterministic & Security Verification")

target_repo = args.get("repo", "agy-sota-harness") if "args" in globals() and isinstance(args, dict) else "agy-sota-harness"

audit = await agent(
    f"Run the two-pass deterministic & P0-P3 self-refuting verification gate on `~/Documents/{target_repo}` "
    f"(`ruff`, `ty`, `sg scan`, `pytest`, `merge_gate.py` if present) and check `~/.agents/bin/sota-bus status --repo {target_repo}`. "
    f"Never print secrets or account IDs.",
    schema=GATE_SCHEMA,
    role=f"Verify {target_repo}",
    type_name="sota-code-verifier",
)

log(f"[{target_repo}] gate_passed={audit['gate_passed']} | P0/P1={len(audit['p0_p1_findings'])}")
print(audit)
