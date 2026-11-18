# ADR-0031: `v3.10.0` Orca Lead (`cc-lead`) E2E SOTA Research Convergence, Finalized `DF1..DF12` Ranking & 10th AGY `run_workflow` DAG

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Antigravity `L0–L13` Harness, Schema-Typed `run_workflow` DAGs (`L5`), 8-Stage SOTA Convergence & 12-Feed Symbol Ranking (`T1–T8`)
- **Evidence Grade:** E4 (`31` GitHub-Evidenced ADRs, `10/10` Schema-Typed AGY `run_workflow` DAGs, `13/13` Live Harness Probes, `pytest` & `merge_gate.py` `0` Leaks Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/stablyai/orca, https://github.com/microsoft/RD-Agent, https://github.com/databento/databento-python
- **Revisit Trigger:** 2026-12-06 (`23/5` Consolidated SIP cutover) or Ecosystem `v4.0.0` promotion

## Context and Problem Statement

Following `ADR-0030` (`9` DAGs), Antigravity (`gemini-4-carbon-high` + `run_workflow`) needed a dedicated 10th schema-typed DAG (`orca_lead_e2e_research_convergence_workflow.py`) validating: (1) finalized `12`-Feed `DF1..DF12` Symbol Ranking DataFeeds (`sota-symbol-ranking-datafeeds.v3.10`) powering `6` autonomous paper routes; (2) `8`-Stage SOTA Convergence backed by `413` owner stars plus `microsoft/RD-Agent`, `databento/databento-python`, `unit8co/darts`, `Nixtla/statsforecast`, `stanfordnlp/dspy`, and `ADIA-Lab/MinTRL-MDE-PowerGate`; and (3) non-colliding Orca Lead (`cc-lead`) E2E task assignment and strict JSON-RPC 2.0 notification silence across MCP servers (`deepseek-flash` default DSH routing).

## Decision Outcome

1. **Add 10th AGY `run_workflow` DAG (`src/agy_sota/workflows/orca_lead_e2e_research_convergence_workflow.py`) & Map in `upstream-map.toml`:**
   - Validate `evaluate_symbol_ranking_to_strategy_handoff()`, `verify_advanced_sota_convergence_practice()`, and `build_orca_lead_e2e_convergence_assignment()` with `PHILOSOPHY_ONLY` sibling authority and `ADR-0022 <= 2.00%` caps.
2. **Advance `SOTA_ECOSYSTEM_MANIFEST.json` (`31` GitHub-Evidenced ADRs) & Enforce Zero-Drift `merge_gate.py`.**

## Alternatives Considered

- **Reusing DAG #9 without a dedicated DF1..DF12 + Orca Lead E2E DAG:** Rejected — dedicated DAG #10 decouples TradingView ergonomics from cross-runtime DF1..DF12 Orca Lead verification cleanly.

## Verification Witness

- `scripts/architecture_catalog.py --sync-manifest && scripts/architecture_catalog.py --check` (`31` ADRs valid, `0` drift)
- `harness/run_probes.py` + `pytest -q` + `scripts/merge_gate.py` (`AGY-MERGE-GATE PASS`, `0` leaks)
