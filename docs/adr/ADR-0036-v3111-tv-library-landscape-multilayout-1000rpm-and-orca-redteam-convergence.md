# ADR-0036: `v3.11.1` TradingView 14-Library Stack, 5-Layout Multi-Surface Coordination, Large-Cap `6–14 bps` Micro-Trail, `1,000 req/min` Exit Reserve & Orca Ecosystem Red-Team Convergence

- **Status:** Accepted
- **Date:** 2026-11-20
- **Layer:** Antigravity `L0–L13` Harness, TradingView Ecosystem Firewall (`L2`/`L6`/`L8`/`L9`), Dual-Workstation Orca Multi-Layout Coordination (`L10`/`L12`) & Adversarial Red-Team Probing
- **Evidence Grade:** E4 (`36` GitHub-Evidenced ADRs, `src/agy_sota/tv_ecosystem_redteam_convergence.py`, `tests/test_tv_ecosystem_redteam_convergence.py` with `500` Hypothesis property examples + `8/8` adversarial red-team firewall probes, `13/13` live harness probes, `merge_gate.py` PASS, `ruff` + `ty` + `gitleaks` `0` leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/sota-mover-ranker, https://github.com/tradingview/lightweight-charts, https://github.com/finos/perspective, https://github.com/OpenBB-finance/backends-for-openbb, https://github.com/deepentropy/tvscreener, https://github.com/PyneSys/pynecore, https://github.com/LuxAlgo/PineTS, https://github.com/cloudflare/security-audit-skill
- **Revisit Trigger:** `2026-12-06` `21:00 ET` `23/5` SIP cutover, TradingView Cloud MCP OAuth/tool schema update, or any modification to `sota-harness-foundation ADR-0045` / `sota-mover-ranker ADR-0068`.

## Context and Problem Statement

Finalizing TradingView multi-layout automation, uncapped 6-preset order coordination (`[P][L][M][B][S][O]`, `TP OFF`), Large-Cap `6–14 bps` micro-trailing with fast sell & suitable-timing Wave-2/3 re-entry, and `1,000 req/min` Alpaca / `3,000 req/min` IBKR `:4002` rate governance across our dual-workstation Orca ecosystem (`sota-harness-foundation ADR-0045`, `sota-mover-ranker ADR-0068`) requires an Antigravity-native, offline-verifiable Red-Team convergence gate (`ADR-0036`) ensuring:

1. Every TradingView library in our researched 14-library stack is classified cleanly under `ADR-0017`'s `4` capability classes with **zero order authority on visual surfaces** and **100% hard refusal of third-party alert-to-broker SaaS relays** (`SignalStack`, `TradersPost`, `PineConnector`, `CrossTrade`, `marketcalls/openalgo`).
2. All `5` multi-surface layouts (`Noesis DISPLAY2`, `DISPLAY1 4K`, `24/5 BOATS`, `OpenBB+Perspective+LWC v5`, `Mac M5 Max Failover`) preserve `>= 92%` unobstructed candles, zero PII/account-ID/home-path leaks, and `singleActiveBrokerHostOnly = true`.
3. Dimensional invariants (`6–14 bps` Large-Cap micro-trail, `5–10 bps` instant `BE+`, `ADR-0022 <= 2.00%`, `take_profit_cap_enabled = False`, `>= 10%` unstarvable protective-exit reserve, live ports `4001`/`7496`/`8796`/`8798` refused, `NaN`/`Inf`/`bool` fail-closed) are continuously verified by deterministic probes and Hypothesis property tests.

## Decision Outcome

1. **Add `src/agy_sota/tv_ecosystem_redteam_convergence.py` (`sota.agy-tv-ecosystem-redteam.v1`):**
   - Implements `verify_largecap_trail_and_rate_bounds()`, `verify_tv_manifest_governance()`, and `run_tv_ecosystem_redteam_probes()` (`8` adversarial probes covering baseline compliance, `ADR-0022 > 2.00%` rejection, `ADR-0063` fixed-TP rejection, all `4` forbidden live ports, `IEEE-754` `NaN`/`Inf`/`bool` fail-closed, third-party SaaS webhook refusal, `< 10%` exit-reserve starvation refusal, and manifest privacy/authority verification).
2. **Add `tests/test_tv_ecosystem_redteam_convergence.py` & Register in `upstream-map.toml`:**
   - Pairs deterministic negative-boundary tests with `500`-example Hypothesis fuzzing of Large-Cap `6–14 bps` / `5–10 bps` / `ADR-0022 <= 2.00%` / `1,000 RPM` invariants and seals `36/36` GitHub-evidenced ADRs in `docs/adr/CATALOG.md` and `SOTA_ECOSYSTEM_MANIFEST.json`.

## Alternatives Considered

- **Testing TradingView Ecosystem Invariants Only Inside Private `sota-mover-ranker`:** Rejected — open-core public CI (`agy-sota-harness` and `sota-harness-foundation`) must continuously enforce the firewall, capability taxonomy, and dimensional bounds independently with zero private-repo dependency.

## Verification Witness

- `uv run python scripts/architecture_catalog.py --sync-manifest && uv run python scripts/architecture_catalog.py --check` (`36 GitHub-evidenced ADRs valid, 0 drift`).
- `uv run python scripts/merge_gate.py` (`AGY-MERGE-GATE PASS`).
- `uv run ruff format --check . && uv run ruff check . && ty check src/agy_sota/tv_ecosystem_redteam_convergence.py && uv run pytest -q && uv run python harness/run_probes.py` (all PASS) & `gitleaks protect --staged --no-banner` (`0` leaks).
