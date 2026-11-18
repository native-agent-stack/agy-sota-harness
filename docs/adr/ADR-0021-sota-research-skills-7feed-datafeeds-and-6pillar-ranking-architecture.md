# ADR-0021: SOTA Research Skills, 7-Feed PIT DataFeeds & 6-Pillar Trading Ranking Architecture (`v3.8.0`)

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Quantitative Research Skills, 7-Feed PIT DataFeeds & 6-Pillar Trading Ranking (`L0–L12` × `P0–P5` × `T0–T8`)
- **Evidence Grade:** E4 (`13/13` AGY Probes, `sota-ranking-and-datafeeds.v2` Hypothesis Suite, `90` HLZ Trials & `60` Compiled Lessons Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-compounding-lab, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/sota-upstream-shelf-lock, https://github.com/nkaz001/hftbacktest, https://github.com/ml4t/diagnostic, https://github.com/skfolio/skfolio
- **Revisit Trigger:** 2027-01-02 or `2026-12-06` `23/5` Consolidated SIP cutover

## Context and Problem Statement

Building on `ADR-0020` (`v3.7.0` Dual-Machine Orca Trading/Harness Lanes DAG `#6` and `>= 11` `orca.yaml` fleet gate), finalizing `v3.8.0` required binding Antigravity's SOTA research and microstructure skills (`microstructure-and-sec-catalyst-lab`, `stockbee-episodic-pivot-analyzer`, `stockbee-momentum-burst-screener`, `sota-quant-research-protocol`, `sota-dimensional-and-property-invariants`, `sota-mover-ranker`) into one authoritative DataFeed and Trading Ranking Architecture (`sota-ranking-and-datafeeds.v2`, `SOTA_ECOSYSTEM_MANIFEST.json` `v3.8.0`).

## Decision Outcome

1. **Skill-to-DataFeed & 6-Pillar Ranking Binding (`SOTA_ECOSYSTEM_MANIFEST.json` `v3.8.0`):**
   - Bind all 7 canonical `sota-research-feeds.v2` PIT DataFeeds (`alpaca_sip` `bs * 100`, `alpaca_boats` `<= 900s`, `alpaca_raw_vs_all_adjustment`, `sec_edgar_acceptance_datetime` `15m` half-life + `S-3`/`424B*` block, `finra_regsho_cnmsshvol_t1` `T-1` + Rule 4560 `T+8` bd, `corporate_actions_split_guard` `XNYS` `bar_age_sessions == 0`, and `ibkr_paper_4002_l1` `2,700/300` reserve) directly into the 6-pillar session-aware SOTA ranking vector (`move`, `unusual_vol` `RVOL_tod`, `inst_dark` `BJZZ 2021`, `iso_urgency` `'F'` ISO + `Lee-Ready OFI`, `overnight`, `catalyst`).
   - Enforce `>= 8h` news silence + `OFI >= 15%` for true `TAPE_PRE_NEWS_IGNITION` (`Gervais-Kaniel-Mingelgrin 2001`), preventing `1h–8h` old intraday headlines from misclassifying as pre-news ignition, and classify candidates by `Trial #90` (`H090`) execution tiers (`TIER1` `<= 10 bps` spread + `>= 25%` `OFI` passive bid: `+20.84 bps` 1x, `5/5` `CPCV`; `TIER2` `<= 35 bps` `H089` two-stage hybrid queue + `50/50` Core+Runner convexity; `TIER3` blocked).
2. **Master Harness × Trading Separation Across 3 Surfaces (`21` MADR 4.0 ADRs):**
   - Keep `Mac M5 Max` dedicated to single-writer Paper execution (`:8787`, `:8799`, `:4002` under `ADR-0022 <= 2.00%` stops) while routing `56`-thread `CPCV` and `29,500`-file pre-wall (`<= 2026-10-15`) sweeps onto `Noesis` Win32 + `* Noesis-Carbon` (`Ubuntu 26.04.1` `ext4`) under `cc-lead` (`oneModelPerConversation = true`).

## Alternatives Considered

1. **Leave SOTA research skills (`stockbee-*`, `microstructure-and-sec-catalyst-lab`) decoupled from the live ranking schema:** Rejected — unifying them inside `sota-ranking-and-datafeeds.v2` guarantees identical PIT, freshness, and stop-cap invariants across screening, backtesting, and live Paper execution.
2. **Allow uncompleted intraday daily bars (`bar_age_sessions < 0`) into EOD burst scoring:** Rejected — hard-blocked by the `XNYS` completed-session freshness gate.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest` -> `21 GitHub-evidenced ADRs valid, 0 drift`
- `python3 scripts/merge_gate.py` -> `[AGY-MERGE-GATE PASS]`
- `uv run pytest -q`, `ruff check .`, & `gitleaks detect --no-git --no-banner` -> `100% PASS` (`0` leaks)
