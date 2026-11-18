# ADR-0022: v3.9.0 9-Feed `sota-ranking-datafeeds.v3.8` (`DF1–DF9`), Dual-Machine Orca Lane Hubs v2 & Full-Landscape Convergence

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Antigravity `L0–L13` Harness, 9-Feed PIT DataFeeds & Dual-Machine Orca Lanes (`H2` / `H4` × `T1–T5`)
- **Evidence Grade:** E4 (`13/13` AGY Probes, `22` ADRs, `64`-Thread `Noesis-Carbon` Pre-Wall Lake SHA-256 & Pytest Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/stablyai/orca, https://github.com/ComposioHQ/agent-orchestrator
- **Revisit Trigger:** 2027-01-02

## Context and Problem Statement

Following `ADR-0020` (Dual-Machine Orca Lanes) and `ADR-0021` (`v3.8.0` Research Skills & 6-Pillar Ranking), converging `agy-sota-harness` onto `v3.9.0` alongside `sota-multi-model-workflows` (`ADR-0016`) and `sota-harness-foundation` (`ADR-0031`) required binding all `6` repository workflows and `14/14` `sota-doctor` layers (`L0–L13`) to the **`9`-feed `sota-ranking-datafeeds.v3.8` (`DF1..DF9`)** contract, the empirical `64`-hex `prewallLakeSha256` (`a253421e873441740d5d4b410d993cfa7345fe34b88ec4ab7f4eecd537b3f234`), and `sota-orca-lane-hub.v2` (`trading-lanes` / `harness-lanes`) RTH broker contention shielding.

## Decision Outcome

1. **Advance `SOTA_ECOSYSTEM_MANIFEST.json` to `3.9.0` & Bind `sota-ranking-datafeeds.v3.8` (`DF1..DF9`):**
   - Enforce 9-feed PIT alignment (`DF1..DF9`) across `L0–L13`, anchoring `prewall_lake_sha256` on `Z:/sota-data/prewall-lake` (`/mnt/z/sota-data/prewall-lake`).
2. **Enforce `sota-dual-machine-lanes.v2` & `sota-orca-lane-hub.v2` (`H2` / `H4`):**
   - Route heavy `agy-sota-harness` test and pre-wall sweeps via `active_broker_host_shield` onto `stationary_noesis_carbon_wsl2` (`64` threads) when `portable_mac_m5_max` holds live `:8787` / `:8799` / `:4002` RTH guardians.

## Alternatives Considered

1. **Retain `7`-feed `sota-research-feeds.v2` as the top-level schema without `DF4` `RVOL_tod`, `DF6` XBRL float, or `DF8` Rule 4560 `T+8`:** Rejected — superseded by `sota-ranking-datafeeds.v3.8` (`ADR-0015`/`ADR-0016`).
2. **Run heavy sweeps locally on `Mac M5 Max` during active RTH paper execution:** Rejected — `active_broker_host_shield` offloads to `* Noesis-Carbon` (`ext4`).

## Verification Witness

- `uv run python scripts/architecture_catalog.py --sync-manifest && uv run python scripts/architecture_catalog.py --check` (`22` ADRs, `0` drift), `uv run python scripts/merge_gate.py`, and `uv run pytest -q` (`PASS`).
