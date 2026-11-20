# ADR-0035: `v3.10.10` Fail-Closed MCP AST Audit, Cross-OS 3-Surface Merge Gate & DAG #10 Offline Fallback Honesty

- **Status:** Accepted
- **Date:** 2026-11-19
- **Layer:** Antigravity `L0–L13` Harness, MCP AST Security Gate (`L2`/`L8`), Cross-OS Privacy Merge Gate (`L9`), Schema-Typed `run_workflow` DAGs (`L5`), & 8-Runtime PreToolUse Parity (`H1–H3`)
- **Evidence Grade:** E4 (`35` GitHub-Evidenced ADRs, `10/10` Schema-Typed AGY `run_workflow` DAGs, `13/13` Live Harness Probes, `60/60` SkillEvaluator Tier-3 Mount Parity PASS across `8/8` runtimes, `sota-doctor` `18/18` Win32 & WSL2, `pytest` + `merge_gate.py` + `gitleaks` `0` Leaks Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/ast-grep/ast-grep, https://github.com/stablyai/orca, https://github.com/K-Dense-AI/scientific-agent-skills, https://github.com/NVIDIA/SkillEvaluator
- **Revisit Trigger:** Any new AGY `run_workflow` DAG beyond `#10`, MCP server addition beyond the `4`-server / `50`-tool mesh, or `ast-grep` / `upstream-map.toml` pin bump.

## Context and Problem Statement

Our four-track cross-vendor full-landscape audit uncovered three silent fallback and privacy-gate defects inside `agy-sota-harness`:

1. **Silent `E4` Inflation on Offline DAG #10 Fallback (`src/agy_sota/workflows/orca_lead_e2e_research_convergence_workflow.py`):** When `sota-multi-model-workflows` (`sota_mmw`) was unavailable in an isolated checkout, DAG #10 silently returned `valid: True` and `evidence_grade: "E4"` from its offline stub instead of explicitly grading the degraded path `E1` with `degraded_offline_fallback: True` and `orca_lead_e2e_ok: False`.
2. **Incomplete Privacy-Gate Coverage & False-Positive Regex (`scripts/merge_gate.py`):** The repository merge gate checked macOS home paths but missed Windows (`C:\Users\<name>`) and Linux (`/home/<name>`) home-path leaks, while its bare `PA[0-9A-Z]{8,14}` regex could match pure uppercase English words like `"PARAMETERS"` rather than requiring at least one digit.
3. **Fail-Open `sota_ast_lint_audit` MCP Fallback & 8-Runtime Firewall Alignment:** The `agy-sota-core` MCP server (`sota_ast_lint_audit`) needed deterministic fail-closed handling when `ast-grep` rules fail to parse or execute, and `SOTA_ECOSYSTEM_MANIFEST.json` needed promotion from `3.10.8` to `3.10.10` locking the `35`-ADR catalog, `8`-runtime upstream-native `PreToolUse` firewalls, and `sota-harness-foundation` `ADR-0044` Tier-3 SHA-256 mount parity.

## Decision Outcome

1. **Enforce Epistemic Honesty in DAG #10 Offline Fallback:** Track `_MMW_IMPORT_DEGRADED` explicitly in `orca_lead_e2e_research_convergence_workflow.py`; when degraded, emit `evidence_grade = "E1"`, `degraded_offline_fallback = True`, `orca_lead_e2e_ok = False`, `deterministic_math_passed = True`, and `all_gates_passed = False` so no downstream promotion consumer mistakes an offline stub for full `E4` E2E verification while still enforcing fail-closed IEEE-754 and `<= 2026-10-15` pre-wall math invariants. Verify all five fields in `tests/test_agy_sota_ecosystem.py`.
2. **Harden Cross-OS 3-Surface Privacy & Secret Detection (`scripts/merge_gate.py`):** Detect macOS, Windows, and Linux concrete home paths uniformly, enforce digit-required Alpaca paper account regex (`PA(?=[0-9A-Z]*[0-9])[0-9A-Z]{8,14}`) eliminating `"PARAMETERS"` false positives, and keep all `18` `upstream-map.toml` shelf pins strictly read-only.
3. **Advance `SOTA_ECOSYSTEM_MANIFEST.json` to `3.10.10` & Lock `35/35` GitHub-Evidenced ADRs:** Add `v31010LandscapeAuditSummary` documenting the `8`-runtime upstream-native firewalls (`AGY`, `Claude`, `Codex`, `Gemini CLI`, `OpenCode + OMO`, `DSH`, `Pi`, `OMP`), `60/60` Tier-3 SHA-256 skill mount parity (`sota-harness-foundation/ADR-0044`), and `18/18` `sota-doctor` verification across Win32 & `Noesis-Carbon` WSL2.

## Alternatives Considered

- **Suppressing Offline Fallback Tests in CI:** Rejected — standalone public GitHub Actions CI runs `agy-sota-harness` without private sibling repos installed; grading the offline stub truthfully as `E1` (`degraded_offline_fallback=True`) preserves standalone CI while preventing false `E4` claims.
- **Checking Only `gitleaks` Without Repo-Local 3-OS Home-Path Regexes:** Rejected — `gitleaks` targets credentials/tokens rather than workstation usernames across Windows/macOS/Linux; `merge_gate.py` must fail closed on all three OS home-path formats.

## Verification Witness

- `uv run python scripts/architecture_catalog.py --sync-manifest` & `--check` (`35 GitHub-evidenced ADRs valid, 0 drift`).
- `uv run python scripts/merge_gate.py` (`AGY-MERGE-GATE PASS`).
- `uv run ruff format --check . && uv run ruff check . && uv run pytest -q` (full suite including DAG #10 degraded-honesty assertions & `13/13` live harness probes PASS) and `gitleaks protect --staged --no-banner` (`0` leaks).
