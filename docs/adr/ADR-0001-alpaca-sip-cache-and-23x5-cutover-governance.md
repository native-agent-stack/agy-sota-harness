# ADR-0001: Alpaca SIP/BOATS Local Lake Entitlement Boundary & Dec-6 `23/5` Cutover Governance

- **Status:** Accepted
- **Date:** 2026-11-17
- **Cross-References:** `meridian` `ADR-0041` (`docs/adr/0041-market-data-stack.md`), `claude-trading-skills` `ADR-0024` & `ADR-0029`, Cross-Family Council Convergence (`Peer Msg #7`, `#8`, `#11`)

## Context & Problem Statement

Across our converged multi-peer stack (`agy-sota-harness`, `cc-sota-harness`, `dsh-sota-harness`, `sota-mover-ranker`, `sota-dynamic-trail-c`, and `meridian`), two governance boundaries required explicit cross-repo reconciliation:

1. **Private Historical Cache & Vendor Cost Discipline (`meridian ADR-0041` vs. `~/Documents/market-data/`):**
   - `~/Documents/market-data/` holds `37 GB` of Consolidated SIP (`bars-1min`, `boats-bars-1min`, `trades`, `quotes`, `published-orb`, `auctions`, `corporate-actions`) plus public SEC EDGAR & FINRA RegSHO tables fetched on owner instruction (`ADR-0024` / `ADR-0029`).
   - `meridian ADR-0041` (`L26–28`) records that **whether a private copy of Alpaca data is permitted under the owner's Alpaca agreement, the feed tier, RPM budget, and any paid vendor remain strictly owner-held contractual decisions**.
2. **December 6, 2026 Consolidated SIP `23/5` Session Cutover:**
   - Alpaca's stated target to transition overnight US equity dissemination from `BOATS` (`20:00–04:00 ET`) to Consolidated SIP `23/5` (`21:00–20:00 ET` with a `20:00–21:00 ET` daily maintenance pause) alters overnight feed routing and session microstructure.

## Decision

1. **Stay on the Sanctioned `$0`-Incremental Stack; Preserve Owner Entitlement Boundary:**
   - Reject `$199/mo` Massive Advanced (`30`-day cache deletion ToS + owner gate) and `$199/mo` Databento Standard (post-wall MBO start + omits `~40%` off-exchange `x == 'D'` FINRA TRF volume).
   - Keep `~/Documents/market-data/` strictly **local, untracked, read-only, non-redistributed, and single-machine**. Contractual interpretation of Alpaca's subscriber agreement remains `OWNER_ENTITLEMENT_BOUNDARY` (`UNVERIFIED` by automated agents; never claim automated legal sign-off).
   - Keep broker-order pacers (`<= 200 req/min` on `PA...` paper accounts, with `15/min` protective-exit reserve) strictly isolated from market-data historical/stream RPM budgets.
2. **Dual-Plane UI & Apache-2.0 Attribution:**
   - Unattended `24/5` HUDs (`:8787` and `:8799`) use self-hosted Apache-2.0 `tradingview/lightweight-charts` (displaying the required `https://www.tradingview.com/` attribution notice) + `finos/perspective`, while `TradingView.app` (`$9.95/mo` US bundle + `24h` toggle) serves as attended human chart & `<= 1–2/day` watchlist sink.
3. **Feature-Flagged `Dec 6, 2026` `23/5` Cutover & Pre-Registered Forward Regime Split:**
   - Gate `2026-12-06` `23/5` SIP session transitions behind `SOTA_ENABLE_DEC6_235_SIP` (`"1"` default, `"0"` instant rollback to `BOATS` `20:00–04:00 ET` if industry cutover slips).
   - Partition all forward paper attribution ledgers into two non-pooled regimes across the cutover boundary:
     - `pre_2026_12_06_24x5_boats` (`<= 2026-12-05`)
     - `post_2026_12_06_23x5_sip` (`>= 2026-12-06`)
4. **macOS `launchd` TCC Boundary & `caffeinate -dimsu` Sleep Guard:**
   - Because macOS TCC blocks non-FDA `launchd` `/bin/bash` wrappers from reading `~/Documents/*` (`exit 78` / `EPERM`), `launchd`-supervised `24/5` daemons must either execute from non-TCC `$HOME` paths (e.g., `~/sota-dynamic-trail-c`) wrapped in `/usr/bin/caffeinate -dimsu`, or run from TCC-authorized interactive sessions wrapped in `/usr/bin/caffeinate -dimsu` verified by `sota-doctor` dead-man checks.
