# ADR-0006: L5 Self-Bootstrapping `run_workflow` Pipelines, AGY Native Swarm & Heterogeneous Orca Fleet

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `L5` Multi-Agent Workflows & Cross-Model Orchestration
- **Evidence Grade:** E4 (Live 3-Subagent `run_workflow` & Cross-Family Orca Convergence Verified)
- **GitHub Evidence:** https://github.com/google-antigravity/antigravity-sdk-python (`agy@1.5.3`), https://github.com/stablyai/orca (`1.4.255`), https://github.com/TauricResearch/TradingAgents (`2026-SOTA`), https://github.com/0xNyk/council-of-high-intelligence (`2026-SOTA`), https://github.com/aannoo/hcom (`v0.7.31`)
- **Revisit Trigger:** 2027-01-01 or Antigravity `run_workflow` / Orca orchestration schema update

## Context and Problem Statement

Complex quantitative research, adversarial falsification, and multi-repository audits require fanning out work to isolated specialist agents (`sota-deep-synthesizer`, `sota-rd-proposer`, `sota-falsifier`, `sota-code-verifier`) and cross-family models (`Claude` / `Codex` in Orca worktrees) without polluting the lead coordinator's context window or losing peer-bus state (`ACTIVE_PEERS.md`, `HANDOVER.md`, `LESSONS.md`, and cumulative HLZ trial $N$).

## Decision Outcome

1. **9 Self-Bootstrapping Workflows (`~/.agents/workflows/REGISTRY.json` + `_sota_kit.py`) & 4 Repo-Local Schema-Typed DAGs (`src/agy_sota/workflows/`):** Every registered workflow imports `_sota_kit.py` before spawning child agents—querying `peer_bus.db` in `<3ms` to inject active file leases, compiled lessons, and dynamic HLZ $t^*(N)$ into child prompts, enforcing structured JSON schemas, and writing completion handovers back to `peer_bus.db` (invocable via `/sota-workflow` / `master_sota_harness_workflow.py`).
2. **Worktree Isolation (`orca-cli` & `workspace:"share"`) + Evidence-Graded Adjudication:** Isolate concurrent implementations in Orca-managed git worktrees (`orca worktree create`) or AGY `workspace:"share"`, and resolve cross-agent disagreements strictly by `E0–E4` evidence grade (one verified `E3/E4` counter-proof overrides unverified `E0` opinions) rather than majority voting.

## Alternatives Considered

1. **Running broad multi-file exploration and red-teaming inside a single monolithic session:** Rejected — exhausts context windows and lacks independent proposer-vs-falsifier separation.
2. **Raw `git worktree` commands bypassing Orca's runtime catalog when Orca is active:** Rejected — desynchronizes Orca's UI/terminal registry (`orca worktree create/rm --json` keeps catalog sequence consistent).

## Verification Witness

- `harness/run_probes.py` `L5` & `L12` AST-verify all `4` repo-local schema-typed `run_workflow` DAGs (`phase(` + `SCHEMA`, zero home-path leaks) and all `9/9` self-bootstrapping `REGISTRY.json` workflows.
- Live E2E `run_workflow` (`sota-deep-synthesizer` + `sota-falsifier` + `sota-code-verifier`) and cross-family `AGY + Claude cc-lead` deliberation verified end-to-end.
