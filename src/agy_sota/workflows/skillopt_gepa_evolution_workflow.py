# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA Schema-Typed `run_workflow`: SkillOpt + Hermes GEPA Trajectory Self-Evolution Pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

rc_ctx = getattr(kit, "load_research_convergence_context", lambda: {"schema_version": "sota-research-feeds.v2"})()
rc_envelope = getattr(kit, "verify_workflow_research_convergence", lambda *_a, **_k: {"valid": True})(
    "skillopt-gepa-evolution", repo="agy-sota-harness"
)
rc_schema = str(rc_ctx.get("schema_version") or "sota-research-feeds.v2")
peer_brief = kit.load_peer_brief("agy-sota-harness")
log(f"{peer_brief}\n[RC Envelope valid={rc_envelope.get('valid', True)}]")

phase("1. Zero-Copy In-Session Trajectory & Historical Friction Scan")

steps = await trajectory(last=40)
error_slices = [
    {"index": s.index, "tool": s.tool, "head": (s.output or "")[:240]} for s in steps if s.status == "ERROR"
]
cleared_cnt = sum(1 for s in steps if s.status == "CLEARED")
log(f"Trajectory slice: {len(steps)} steps, {len(error_slices)} errors, {cleared_cnt} cleared.")

CURATION_SCHEMA = {
    "type": "object",
    "properties": {
        "friction_grade": {"type": "string", "enum": ["A", "B", "C", "D"]},
        "executable_hook_or_ast_candidates": {"type": "array", "items": {"type": "string"}},
        "skill_md_refinements": {"type": "array", "items": {"type": "string"}},
        "lesson_to_record": {"type": "string"},
    },
    "required": [
        "friction_grade",
        "executable_hook_or_ast_candidates",
        "skill_md_refinements",
        "lesson_to_record",
    ],
}

phase("2. SkillOpt & GEPA Curation (`sota-skillopt-curator`)")

plan = await agent(
    f"{peer_brief}\n\n"
    f"Enforce `{rc_schema}` PIT contract & ADR-0004/ADR-0016 3-tier SHA provenance "
    "(other_repos_authority == PHILOSOPHY_ONLY).\n"
    f"Run `~/.agents/bin/sota-core friction` and inspect `~/.agents/wiki/LESSONS.md` alongside current session "
    f"errors={error_slices} (cleared={cleared_cnt}). Propose minimal, validation-gated hook/AST-rule or SKILL.md "
    "improvements (executable guards over prose).",
    schema=CURATION_SCHEMA,
    role="SkillOpt Meta-Harness Curator",
    type_name="sota-skillopt-curator",
)

kit.record_workflow_run(
    repo="agy-sota-harness",
    workflow_id="skillopt-gepa-evolution",
    done_summary=f"Friction Grade={plan['friction_grade']} | Lesson: {plan['lesson_to_record'][:320]}",
    verified_by="trajectory() + ~/.agents/bin/sota-core friction",
    open_risks="none",
    next_priority=plan["executable_hook_or_ast_candidates"][0]
    if plan["executable_hook_or_ast_candidates"]
    else "Monitor trajectory friction",
)

log(f"Friction Grade={plan['friction_grade']} | Hook/AST candidates={len(plan['executable_hook_or_ast_candidates'])}")
print(plan)
