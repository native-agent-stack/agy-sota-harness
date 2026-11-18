# ADR-0016: End-to-End SOTA Research-Convergence Contract Across Workflows, 7-Feed PIT DataFeeds & Strategy Templates

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Cross-Cutting Research, DataFeeds, Strategy Templates & Workflows (`L4–L12` × `T1–T8` × `P0–P5`)
- **Evidence Grade:** E4 (Runtime-Verified Across `agy-sota-harness`, `sota-multi-model-workflows`, `sota-compounding-lab`, `trading-sota`, `astrolabe` & `sota-mover-ranker`)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-compounding-lab, https://github.com/native-agent-stack/astrolabe, https://github.com/alpacahq/alpaca-py (`c42add7c0a7026e2ead3ed64e76f4def2b99fda4`), https://github.com/dgunning/edgartools (`574c2bd15f6c629bceef03b6550ea8ac8abf3473`), https://github.com/nautechsystems/nautilus_trader (`da6b57aefdd62b44f675e434ffcfefca7f4025dd`)
- **Revisit Trigger:** 2027-01-02 (45-day cadence), `2026-12-06` Consolidated SIP `23/5` cutover, or any upstream `PINS.md` SHA bump

## Context and Problem Statement

Research-convergence principles (`ADR-0004`: 64-hex SHA-256 input snapshot + 40-hex pinned upstream commit + reproducible command + `E0–E4` evidence grade, with sibling repositories treated strictly as `PHILOSOPHY_ONLY`) and 7-feed point-in-time market-data rules (`SIP` + `BOATS` + `RAW`/`ALL` split invariance + SEC `acceptanceDateTime` + FINRA `T-1` `asof`) cannot rely on prose alone. Without executable validators inside strategy templates, MCP servers, trading-lane DataFeed adapters, and `run_workflow` bootstraps, individual templates drift (e.g., non-PIT defaults or `> 2.00%` stop placeholders) and workflows fail to query live first-hand catalyst feeds.

## Decision Outcome

1. **Executable Research-Convergence & Strategy-Template Validator (`src/agy_sota/research_convergence.py` & `templates/sota_converged_strategy.template.json`):**
   - Enforce `sota-converged-strategy.v1` across all 4 canonical archetypes (`PRE_TRAVEL_EARLY_IGNITION`, `FIRST_HAND_SEC_EPISODIC_PIVOT`, `MEGA_CAP_NEAR_LOSSLESS_ORB`, `CLIMAX_VWAP_MEAN_REVERSION`), verifying 40-char Git SHAs directly against `[shelf_pins]` in `upstream-map.toml`, `other_repos_authority == "PHILOSOPHY_ONLY"`, `<= 2026-10-15` pre-wall isolation, HLZ dynamic `t*(N)`, `5`-path purged `CPCV` (`PBO <= 0.30`), `DSR >= 0.95`, `ADVERSE_STOP_FIRST` queue tie-breaking, `[1.0, 2.0]` impact stress, non-repainting Pine v6 (`barstate_confirmed_only=True`), and `ADR-0022 <= 2.00%` paper-only stops (`PA... <=200/min`, `DU... :4002 <=3,000/min`).
2. **Unified 7-Feed PIT DataFeed Contract (`sota-research-feeds.v2`) & MCP Exposure:**
   - Standardize `resolve_session_datafeed()` (`04:00–20:00 ET` `sip` vs `20:00–04:00 ET` `boats` + `2026-12-06` `23/5` feature flag), `Adjustment.RAW` nominal price/volume gates vs `Adjustment.ALL` forward returns (`[-1, +3]` split guard), SEC EDGAR `acceptanceDateTime` (`15m` half-life + `S-3`/`424B5` dilution block), and FINRA `CNMSshvol` `T-1` `asof` across `agy-sota-harness`, `trading-sota`, `sota-compounding-lab`, `astrolabe`, and `sota-mover-ranker-stdio` MCP (`sota_get_research_feeds`, `sota_get_first_hand_incentives`, `sota_get_converged_strategy_templates`).
3. **Turn-0 Workflow Bootstrap & Dedicated Landing Pipeline (`research_convergence_landing_workflow.py`):**
   - Inject the 7-feed PIT DataFeed & `ADR-0004` convergence contract into `_sota_kit.py` across all 13 global multi-model workflows (`~/.agents/workflows/REGISTRY.json`) and 5 repo-local `agy-sota-harness` workflows.

## Alternatives Considered

1. **Keeping research convergence as prose checklists inside `AGENTS.md` / `ADR-0004`:** Rejected — prose checklists did not prevent legacy `_template/manifest.json` drift (`pointInTime: false`, `10%` stop) or missing MCP feed tools.
2. **Copying hardcoded alpha weights across repositories:** Rejected — violates `ADR-0004` (`other_repos_authority == "PHILOSOPHY_ONLY"`) and leaks private empirical parameters into public open-core harnesses.

## Verification Witness

- `mise exec -- uv run python scripts/architecture_catalog.py --check` -> `16 GitHub-evidenced ADRs valid, 0 drift`
- `mise exec -- uv run python scripts/merge_gate.py` -> `[AGY-MERGE-GATE PASS]`
- `mise exec -- uv run python harness/run_probes.py` -> `13/13 probes PASSED` (`5` repo-local workflows, `16` bridged repos)
- `mise exec -- uv run pytest -q` -> `100%` PASS
