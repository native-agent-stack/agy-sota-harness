# ADR-0032: `v3.10.3` Fail-Closed DAG #10 Fallback Guard & `2026-10-15` Nanosecond Epoch Alignment

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Antigravity `L0–L13` Harness, Schema-Typed `run_workflow` DAGs (`L5`), Pre-Wall Bitemporal & IEEE-754 Fail-Closed Guards (`T1–T8`)
- **Evidence Grade:** E4 (`32` GitHub-Evidenced ADRs, `10/10` Schema-Typed AGY `run_workflow` DAGs, `13/13` Live Harness Probes, `pytest` & `merge_gate.py` `0` Leaks Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-compounding-lab
- **Revisit Trigger:** 2026-12-06 (`23/5` Consolidated SIP cutover) or Ecosystem `v4.0.0` promotion

## Context and Problem Statement

An adversarial cross-repo audit (`cc-lead-e2e-review` `#291`/`#292`) caught two defects in DAG #10 (`src/agy_sota/workflows/orca_lead_e2e_research_convergence_workflow.py`):
1. **Fail-open `ImportError` fallback:** When `sota_mmw` was not installed (e.g., clean CI checkout), the fallback `evaluate_symbol_ranking_to_strategy_handoff` unconditionally returned `{"approved": True}` without checking study-wall, bitemporal ordering, IEEE-754 finiteness, or `ADR-0022 <= 2.00%` stop caps.
2. **Epoch year drift:** The sample nanosecond timestamps (`1_760_500_000_000_000_000`) corresponded to `2025-10-15` instead of `study_date="2026-10-15"`.

## Decision Outcome

1. **Fail-closed fallback verifier:** The `ImportError` fallback now enforces `study_date <= 2026-10-15`, non-bool integer `ts_event_ns <= ts_recv_ns <= decision_ns`, UTC `decision_ns` study-wall & `study_date` match, finite IEEE-754 checks (`OverflowError`/NaN/Inf safe), `H096` `15.0s` / `<= 10.0 bps` dry-powder collar, and `ADR-0022` `0.05% <= hard_stop_pct <= 2.00%`.
2. **Exact `2026-10-15T14:30:00Z` nanosecond epoch:** Updated sample timestamps to `1_792_074_600_000_000_000` (`+5ms` / `+10ms`), aligned with `study_date="2026-10-15"`.
3. **Stage-5 Lossless `L1` probe alignment:** Updated `harness/run_probes.py` `probe_l1()` so live-endpoint hooks (`~/.claude/bin/live`, `api.alpaca.markets`, port `4001`) verify gated `decision in ("ask", "deny")` (compatible with both owner Stage-5 `PreToolUse` `ask` approval and hard `deny` hosts), while keeping `~/Documents/upstream/` immutable shelf mutation strictly `deny`.
4. **Regression test & `SOTA_ECOSYSTEM_MANIFEST.json` parity (`32` GitHub-evidenced ADRs).**

## Alternatives Considered

- **Removing the `ImportError` fallback entirely:** Rejected — clean-checkout CI runs `agy-sota-harness` independently without requiring an editable install of sibling `sota-multi-model-workflows`.

## Verification Witness

- `scripts/architecture_catalog.py --sync-manifest && scripts/architecture_catalog.py --check` (`32` ADRs valid, `0` drift)
- `harness/run_probes.py` + `pytest -q` + `scripts/merge_gate.py` (`AGY-MERGE-GATE PASS`, `0` leaks)
