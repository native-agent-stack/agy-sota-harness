# ADR-0025: v3.9.3 Unified 46-Skill Cross-Harness Convergence, 7th AGY Grand Workflow DAG & Dual-Machine Orca Automations

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Antigravity `L0–L13` Harness, 46-Skill Triad/Orca Mesh & Schema-Typed `run_workflow` DAGs (`H2` / `H4` × `T1–T5`)
- **Evidence Grade:** E4 (`46/46` Canonical Skills Converged Across AGY+Claude+Codex+Orca, `7/7` AGY `run_workflow` DAGs, `13/13` Probes & `21/21` Pytest Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/cc-sota-harness, https://github.com/stablyai/orca
- **Revisit Trigger:** 2027-01-02

## Context and Problem Statement

Prior to `v3.9.3`, `29` SOTA quantitative, catalyst-screening, risk/postmortem, and scientific skills resided inside Antigravity plugin/vendored folders without full `1:1` convergence into `~/.agents/skills`, Claude Code (`~/.claude/skills`), Codex (`~/.codex/skills`), and `orca skills installed` across `Mac M5 Max`, `Stationary Noesis Win32`, and `Noesis-Carbon` WSL2.

## Decision Outcome

1. **Converge All `46` Canonical SOTA Skills Across AGY, Claude Code, Codex, and Orca (`L2` / `L4`):**
   - Materialize all `46` SOTA skills (`18` Core/Orchestration + `20` Quant/Early-Mover + `8` Scientific/Security) in `~/.agents/skills` and mount across `~/.gemini/config/skills`, `~/.claude/skills`, `~/.codex/skills`, and `orca skills installed` (`46/46` matched).
2. **Add 7th Schema-Typed AGY `run_workflow` Pipeline & Advance `manifestVersion` to `"3.9.3"` (`25` ADRs):**
   - Ship `src/agy_sota/workflows/sota_skills_adr_and_orca_grand_workflow.py` bound to `sota-multi-model-workflows` `ADR-0018` (`~/.agents/bin/sota-workflow`, `17` workflows, `14` layers, `18`-repo ADR router, and Dual-Machine Orca Automations).

## Alternatives Considered

- **Leaving `29` quant/scientific skills Antigravity-only:** Rejected; multi-model Orca child worktrees require uniform skill availability across all `7` model vendors.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` -> `25 GitHub-evidenced ADRs valid, 0 drift`
- `python3 harness/run_probes.py` -> `13/13 probes PASSED` (`46` canonical skills, `7` AGY `run_workflow` pipelines)
- `pytest -q && python3 scripts/merge_gate.py && gitleaks git --staged --no-banner` -> `21 passed`, `[AGY-MERGE-GATE PASS]`, `0` leaks
