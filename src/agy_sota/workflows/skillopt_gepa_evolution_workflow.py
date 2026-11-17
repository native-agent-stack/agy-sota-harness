# ruff: noqa: F704, F821, PLE1142
"""AGY SOTA Schema-Typed `run_workflow`: SkillOpt + Hermes GEPA Trajectory Self-Evolution Pipeline."""

phase("1. Zero-Copy In-Session Trajectory & Historical Friction Scan")

steps = await trajectory(last=40)
error_slices = [
    {"index": s.index, "tool": s.tool, "head": (s.output or "")[:240]}
    for s in steps
    if s.status == "ERROR"
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
    f"Run `~/.agents/bin/sota-core friction` and inspect `~/.agents/wiki/LESSONS.md` alongside current session "
    f"errors={error_slices} (cleared={cleared_cnt}). Propose minimal, validation-gated hook/AST-rule or SKILL.md "
    f"improvements (executable guards over prose).",
    schema=CURATION_SCHEMA,
    role="SkillOpt Meta-Harness Curator",
    type_name="sota-skillopt-curator",
)

log(f"Friction Grade={plan['friction_grade']} | Hook/AST candidates={len(plan['executable_hook_or_ast_candidates'])}")
print(plan)
