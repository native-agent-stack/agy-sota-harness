# ADR-0018: `v3.5.0` Claude Code (`cc-lead`) Central 14-Workflow Hub, `Noesis` `15/15` Co-op & Full-Landscape Manifest Convergence

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Runtime Orchestration, Cross-Workstation Parity & Trading Ecosystem Governance (`L0–L12` × `P0–P5` × `T0–T8`)
- **Evidence Grade:** E4 (`13/13` AGY Probes, `sota-doctor` `12/12 PASS`, `sota-org-doctor --live` `22/22 PASS`, `Mac M5 Max + Noesis` `15/15` Hub Runtimes & Live `run_workflow` Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/native-agent-stack, https://github.com/stablyai/orca, https://github.com/ComposioHQ/agent-orchestrator
- **Revisit Trigger:** 2027-01-02

## Context and Problem Statement

Following `ADR-0017` (`Trial #89 H089` Two-Stage Hybrid Entry × `50/50` Asymmetric Runner Convexity across `587` pre-wall dates), `SOTA_ECOSYSTEM_MANIFEST.json` remained pinned to `manifestVersion = "3.3.0"` (`13` workflows, `82`-trial vault metadata, and pre-`v3.5.0` repository SHAs), while the live organization had converged on `v3.5.0`: `14` self-bootstrapping workflows (including Workflow `#14` `cc_lead_multi_runtime_workers_workflow.py` and `sota-cc-hub`), cross-OS `darwin`/`win32` `15/15` runtime binary parity across `Mac M5 Max` and `Noesis`, `89` pre-registered trials (`t*(90) = 4.1735`), `52` compiled `E1–E4` lessons, and live post-Gain-Lock `50/50` runner convexity on `:8787` / `:8799`.

## Decision Outcome

1. **Upgrade `SOTA_ECOSYSTEM_MANIFEST.json` to `manifestVersion = "3.5.0"` (`18` MADR 4.0 ADRs):**
   - Synchronize all `18` active `githubFleetRepositories` entries to their `v3.5.0` roles and converged commits (`native-agent-stack` `ADR-0011+`, `sota-harness-foundation` `ADR-0026`, `cc-sota-harness` `ADR-0024`, `sota-multi-model-workflows` `v3.5.0` `14` workflows `@ 2cc19d52cfb5`, `sota-mover-ranker` `ADR-0011` `@ 00f132cf`, `sota-dynamic-trail-c` `v1.0.1` `ADR-0010`, and `sota-private-vault` `89` trials / `52` lessons).
2. **Co-Operate `Antigravity` (`P0`) Seamlessly Inside the `cc-lead` (`P1`) 5-Channel Runtime Hub:**
   - Keep Claude Code (`cc-lead`, `claude-fable-5-2` `xhigh` + `oh-my-claudecode` `OMC` Runtime v2, `oneModelPerConversation = true`) as central multi-session orchestrator while `Antigravity` (`gemini-4-carbon-high`) serves as the 1M-context `18`-clone upstream-shelf synthesizer, `run_workflow` DAG executor (`14/14` workflows), and 3rd concrete frontier vendor in Stage-3+ multi-family reviews (`omc ask antigravity`, `orca orchestration worker-start --agent antigravity`).

## Alternatives Considered

1. **Leave `SOTA_ECOSYSTEM_MANIFEST.json` frozen at `3.3.0` while `REGISTRY.json` and `native-agent-stack` run `3.5.0`:** Rejected — creates cross-repo manifest version skew between `L4` (`agy-sota-harness`) and `L1`/`L7` (`native-agent-stack` / `sota-multi-model-workflows`).
2. **Duplicate `cc_lead_hub.py` inside `agy-sota-harness`:** Rejected — violates `One-Owner-Per-Layer` (`L7` `sota-multi-model-workflows` owns `sota_mmw.cc_lead_hub` and `~/.agents/bin/sota-cc-hub`).

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest` -> `18 GitHub-evidenced ADRs valid, 0 drift`
- `python3 scripts/merge_gate.py` -> `[AGY-MERGE-GATE PASS]`
- `python3 harness/run_probes.py` -> `13/13 probes PASSED` (`14/14 workflows` verified)
- `uv run pytest -q`, `ruff`, `ty`, & `gitleaks detect --no-git --no-banner` -> `100% PASS` (`0` leaks)
