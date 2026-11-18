# ADR-0013: Alpaca SIP/BOATS Local Lake Entitlement Boundary & Dec-6 `23/5` Cutover Governance

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `T1–T8` Market-Data Governance, Pacer Isolation & Session Cutover
- **Evidence Grade:** E3 (Cross-Family Council Converged + Feature-Flagged & Pre-Registered as `Trial #81`)
- **GitHub Evidence:** https://github.com/alpacahq/alpaca-py (`c42add7c0a7026e2ead3ed64e76f4def2b99fda4`), https://github.com/gerrymanoim/exchange_calendars (`dbe38b1f6887434bbdd1a7d2df6ff8f1742a048a`), https://github.com/ib-api-reloaded/ib_async (`ab629f34c1823ea4c1542f32f07377208a86bdfd`), https://github.com/native-agent-stack/sota-mover-ranker (`bb1d90b10a95333975ced7e4d16c59d5e67f5e94`), https://github.com/native-agent-stack/sota-dynamic-trail-c (`584f22b4dba65819c538734a5f2bdf569c900566`)
- **Revisit Trigger:** 2026-12-06 Consolidated SIP `23/5` go-live confirmation or owner market-data vendor amendment

## Context and Problem Statement

Across our converged multi-peer stack (`agy-sota-harness`, `cc-sota-harness`, `dsh-sota-harness`, `sota-mover-ranker`, `sota-dynamic-trail-c`, and `meridian`), two governance boundaries required explicit cross-repo reconciliation: (1) reconciling the `37 GB` local `~/Documents/market-data/` cache (`bars-1min`, `boats-bars-1min`, `trades`, `quotes`, `published-orb`, `auctions`, `corporate-actions`, SEC EDGAR, FINRA RegSHO) with `meridian ADR-0041` vendor/entitlement rules, and (2) handling the targeted December 6, 2026 transition from overnight `BOATS` (`20:00–04:00 ET`) to Consolidated SIP `23/5` (`21:00–20:00 ET` with a `20:00–21:00 ET` daily pause) without silent session drift or pooled attribution distortion.

## Decision Outcome

1. **Stay on the Sanctioned `$0`-Incremental Stack & Preserve Owner Entitlement Boundary:**
   - Reject `$199/mo` Massive Advanced (`30`-day cache deletion ToS + owner gate) and `$199/mo` Databento Standard (post-wall MBO start + omits `~40%` off-exchange `x == 'D'` FINRA TRF prints).
   - Keep `~/Documents/market-data/` strictly local, untracked, read-only, non-redistributed, and single-machine; subscriber-agreement interpretation remains an `OWNER_ENTITLEMENT_BOUNDARY` (`UNVERIFIED` by automated agents).
   - Isolate broker-order pacers (`<= 200 req/min` on `PA...` paper accounts with `15/min` protective-exit reserve) strictly from historical/streaming market-data RPM budgets, and block new autonomous paper entries on `XNYS` full holidays (`exchange_calendars@4.13.2`).
2. **Default-Off Feature-Flagged `Dec 6, 2026` `23/5` Cutover & Pre-Registered Regime Split (`Trial #81`):**
   - Gate `2026-12-06` `23/5` SIP session routing behind `SOTA_ENABLE_DEC6_235_SIP` (default `"0"` until exchange go-live is verified, `"1"` enabling `21:00–20:00 ET` SIP + `20:00–21:00 ET` pause).
   - Partition forward paper attribution ledgers into non-pooled `pre_2026_12_06_24x5_boats` (`<= 2026-12-05`) vs `post_2026_12_06_23x5_sip` (`>= 2026-12-06`) regimes (`FWD_REGIME_SPLIT_DEC6_2026_23X5_SIP_CUTOVER`, SHA-256 `02fe81ed20c4...`).

## Alternatives Considered

1. **Purchasing `$199/mo` Databento Standard or Massive Advanced subscriptions:** Rejected by unanimous 3-Seat AGY Council + `Claude cc-lead` review (`Peer Msg #7`, `#8`, `#11`) due to TRF dark-pool omission, `30`-day cache-deletion terms, and zero incremental pre-wall power gain over the existing `37 GB` SIP + SEC/FINRA lake.
2. **Unconditional calendar-date switch on `2026-12-06` without a feature flag:** Rejected — exchange cutovers can slip; explicit flag + regime split prevents silent routing bugs.

## Verification Witness

- `docs/adr/ADR-0013-alpaca-sip-cache-and-23x5-cutover-governance.md` verified in `CATALOG.md`; `sota-mover-ranker@9ba23e0` (`38/38` `pytest`) and `sota-dynamic-trail-c@bc50ae8` (`29/29` `pytest`) enforce `<= 200/min` order pacing, holiday blocks, and `SOTA_ENABLE_DEC6_235_SIP`.
