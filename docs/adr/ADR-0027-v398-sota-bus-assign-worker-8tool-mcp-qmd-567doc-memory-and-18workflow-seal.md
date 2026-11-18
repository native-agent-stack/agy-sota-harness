# ADR-0027: `v3.9.8` `sota_bus_assign_worker` `8`-Tool Peer-Bus MCP, `567`-Doc `qmd` Memory Index, `8` AGY Workflow DAGs & Trial `#96` (`H096`) Co-op Seal

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Antigravity `L0–L13` Harness, Peer-Bus Memory (`L3`/`L7`) & Multi-Model Orchestration (`L5`/`L10`/`L11`)
- **Evidence Grade:** E4 (`27` ADRs, `13/13` AGY Probes, `8` Schema-Typed AGY Workflow DAGs, `8`-Tool `sota-peer-bus` MCP & `96` Pre-Registered HLZ Trials `t*(97) = 4.1905`)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/stablyai/orca, https://github.com/tobi/qmd
- **Revisit Trigger:** 2027-01-02 or Ecosystem `v4.0.0` promotion

## Context and Problem Statement

Following `ADR-0026` (`v3.9.7`), Antigravity (`agy`) required a 1-call multi-model task dispatcher (`sota_bus_assign_worker`) in `sota-peer-bus` MCP, local `qmd` indexing across all `563` MADR 4.0 ADRs + `4` wiki ledgers (`567` total docs), `8` embedded AGY `run_workflow` DAGs (adding `multi_model_omc_memory_assign_workflow.py` `#18`), and alignment with pre-registered Trial `#96` (`H096_DRY_POWDER_15S_BID_SURVIVAL_10BPS_COLLAR_ORB_CPCV`, `spec_sha256 = 588d27755bad...`).

## Decision Outcome

1. **Expose `8` Tools in `sota-peer-bus` MCP (`sota_bus_assign_worker`) & Add `8th` AGY DAG (`multi_model_omc_memory_assign_workflow.py`):**
   - Enable Antigravity to assign tasks in 1 call across all `7` model vendors (`claude`, `codex`, `omp`, `opencode`, `muse`, `grok`, `antigravity`, `cc-lead`, `noesis-cc-lead`) across `Mac M5 Max` and `Noesis` (`100.110.115.22`) with `--spec-file -` FTS5 + `qmd` (`567`-doc) memory brief, disjoint lease claim, and `worker-release`.
2. **Codify `Trial #96` (`H096`) Governance Transition (`v3.9.8`, `N = 96 -> t*(97) = 4.1905`):**
   - Wide `OFI > 0` (`n = 124`, `-12.729 bps` net `1x`, `t = -0.7781`) failed `ALPHA_STRATEGY_MINOR`, while strict `OFI >= 0.25 & (ISO_F >= 0.15 | BJZZ >= 0.12)` + `15s` dry-powder bid-survival + `<= 10.0 bps` collar (`n = 52` / `47d`, `+16.835 bps` net `1x` / `+11.366 bps` net `2x`, `11/15 = 73.33%` CPCV `> 0`) is preserved under `PROTECTIVE_FILTER_OR_GOVERNANCE` (`v3.9.8`).

## Alternatives Considered

- **Leaving `sota-peer-bus` at `7` tools without native task assignment:** Rejected — forced manual shell glue instead of schema-validated 1-call multi-model delegation.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` -> `27 GitHub-evidenced ADRs valid, 0 drift`
- `python3 harness/run_probes.py` -> `13/13 probes PASSED`
- `uv run pytest -q && python3 scripts/merge_gate.py && gitleaks git --staged --no-banner` -> `PASS`, `[AGY-MERGE-GATE PASS]`, `0` leaks
