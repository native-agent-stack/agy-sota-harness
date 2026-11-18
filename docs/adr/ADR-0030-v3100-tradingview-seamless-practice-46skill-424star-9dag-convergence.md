# ADR-0030: `v3.10.0` TradingView Seamless Practice (`46` Skills + `424` Stars), `9th` AGY `run_workflow` DAG & Win32 WireGuard Bootstrap

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Antigravity `L0–L13` Harness, Schema-Typed `run_workflow` DAGs (`L5`), Starred Visual/Quant Craft (`L6`/`L8`) & Dual-Workstation TradingView Practice (`T1–T8`)
- **Evidence Grade:** E4 (`30` GitHub-Evidenced ADRs, `9/9` Schema-Typed AGY `run_workflow` DAGs, `13/13` Live Harness Probes, `pytest` & Live `Noesis` `run_workflow` Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-mover-ranker, https://github.com/native-agent-stack/sota-dynamic-trail-c, https://github.com/vercel-labs/agent-desktop, https://github.com/tradingview/lightweight-charts, https://github.com/finos/perspective, https://github.com/likec4/likec4, https://github.com/NVIDIA/SkillEvaluator, https://github.com/elementalsouls/Claude-BugHunter
- **Revisit Trigger:** 2027-01-02 or Ecosystem `v4.0.0` promotion

## Context and Problem Statement

1. **Cross-OS `run_workflow` Bootstrap & Live `:8787` Telemetry on Stationary `Noesis` (`100.110.115.22`):**
   - Under `singleActiveBrokerHostOnly = True` (`ADR-0020`), `Mac M5 Max` (`100.93.211.101`) is the sole active `:8787`/`:8799`/`:4002` paper broker host, while Stationary `Noesis` (`3840×2160 @ 120Hz` primary `DISPLAY2` + secondary `4K` `DISPLAY1` wall + `:8792` push receiver) owns primary interactive `TradingView.exe` display. Antigravity needed a dedicated schema-typed `run_workflow` pipeline uniting `sota-dynamic-trail-c` `ADR-0023` (`sota-tv-seamless-practice.v2`), `sota-mover-ranker` `ADR-0028` (`sota.tv-seamless-practice-convergence.v2` + Protobuf-safe `17`-tool MCP), `46` canonical research skills, and the `424`-row starred SOTA repository atlas seamlessly from either workstation.

## Decision Outcome

1. **Ship `9th` Schema-Typed Antigravity `run_workflow` Pipeline (`src/agy_sota/workflows/tradingview_seamless_practice_convergence_workflow.py`):**
   - Self-bootstraps `sota-research-feeds.v2` (`PHILOSOPHY_ONLY` sibling-repo authority) + live `:8787/api/tv/seamless_practice` and `:8792/healthz` over loopback or Tailscale WireGuard (`100.93.211.101` / `100.110.115.22`), supports `<1s` `fast_deterministic_only` prechecks, and orchestrates parallel `sota-deep-synthesizer` + `sota-falsifier` + `sota-code-verifier` gates verifying `DF5` SEC dilution hard-blocks, `0-WS` Wave-2 L1 quote/OBI integrity, `H096 <= 10.0 bps` `15s` dry-powder collar, `stage1_rvol_tod >= 2.20`, `ADR-0022 <= 2.00%` stops, and `DISPLAY2` `120Hz` zero-focus-steal ergonomics.
2. **Sync `SOTA_ECOSYSTEM_MANIFEST.json` (`30` ADRs, `9` AGY `run_workflow` DAGs, `49`-Tool `4`-Server MCP Mesh):**
   - Preserves `17 + 8 + 7 + 17 = 49` live Protobuf-safe MCP tools across `sota-mover-ranker`, `sota-peer-bus`, `agy-sota-core`, and `codebase-memory`.

## Alternatives Considered

- **Ad-hoc manual subagent prompts without a versioned `src/agy_sota/workflows/` DAG:** Rejected — deterministic `probe_l5` AST/Research-Convergence checks guarantee zero drift across Mac and Noesis.

## Verification Witness

- `python scripts/architecture_catalog.py --sync-manifest && python scripts/architecture_catalog.py --check` (`30` GitHub-evidenced ADRs valid, `0` drift)
- `python harness/run_probes.py` (`13/13 probes PASSED`)
- `pytest -q` (`22 passed`), `ruff check .`, `python scripts/merge_gate.py` (`AGY-MERGE-GATE PASS`), and `gitleaks` (`0` leaks)
