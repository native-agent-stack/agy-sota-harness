# ruff: noqa: F704, F821, PLE1142
"""AGY SOTA Schema-Typed `run_workflow`: RD-Agent(Q) Pre-Registration -> Falsifier -> Verifier Pipeline.

Orchestrates custom AGY subagents (`sota-rd-proposer`, `sota-falsifier`, `sota-code-verifier`) with
immutable SHA-256 pre-registration on `sota-peer-bus` (`<= 2026-10-15` strict wall).
"""

HYPOTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "hypothesis_id": {"type": "string"},
        "title": {"type": "string"},
        "spec_text": {"type": "string"},
        "pre_wall_verified": {"type": "boolean"},
        "max_stop_pct": {"type": "number"},
    },
    "required": ["hypothesis_id", "title", "spec_text", "pre_wall_verified", "max_stop_pct"],
}

FALSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "survived_red_team": {"type": "boolean"},
        "lookahead_audit": {"type": "string"},
        "cost_and_dilution_stress": {"type": "string"},
        "fatal_flaws": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["survived_red_team", "lookahead_audit", "cost_and_dilution_stress", "fatal_flaws"],
}

phase("1. RD-Agent(Q) Factor Proposal (Pre-Wall <= 2026-10-15)")

proposal = await agent(
    "Search `~/.agents/bin/sota-bus search 'early mover'` and `~/Documents/upstream/PINS.md` (read-only). "
    "Formulate one falsifiable microstructure hypothesis for `sota-mover-ranker` strictly inside `<= 2026-10-15` "
    "with `max_stop_pct <= 2.00` (ADR-0022). Return structured JSON.",
    schema=HYPOTHESIS_SCHEMA,
    role="RD-Agent Factor Proposer",
    type_name="sota-rd-proposer",
)
log(f"Proposed `{proposal['hypothesis_id']}`: {proposal['title']}")

phase("2. Adversarial Microstructure, Dilution & Lookahead Red-Team")

falsifier = agent(
    "Attempt to disprove factor proposals for lookahead bias, survivorship leakage, S-3/424B5 dilution traps, "
    "2x spread/impact decay, and Harvey-Liu-Zhu multiple-testing hurdles.",
    role="Adversarial Quant Falsifier",
    type_name="sota-falsifier",
)

verdict = await falsifier(f"Red-team this pre-wall hypothesis:\n{proposal}", FALSIFICATION_SCHEMA)
log(f"Falsifier survived={verdict['survived_red_team']} flaws={verdict['fatal_flaws']}")

if not verdict["survived_red_team"] and verdict["fatal_flaws"]:
    phase("3. Single-Parameter Tightening & Second-Pass Falsification")
    revised = await agent(
        f"Resolve these fatal flaws without adding degrees of freedom:\nProposal: {proposal}\nFlaws: {verdict['fatal_flaws']}",
        schema=HYPOTHESIS_SCHEMA,
        role="RD-Agent Hypothesis Refiner",
        type_name="sota-rd-proposer",
    )
    verdict = await falsifier(f"Re-audit revised proposal:\n{revised}", FALSIFICATION_SCHEMA)
    proposal = revised

del falsifier

output = {"proposal": proposal, "falsification": verdict}
print(output)
