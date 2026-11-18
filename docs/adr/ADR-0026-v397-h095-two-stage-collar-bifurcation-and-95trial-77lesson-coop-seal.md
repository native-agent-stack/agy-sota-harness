# ADR-0026: v3.9.7 Pre-Registered Trial `#95` (`H095`) Stage-1/Stage-2 Execution Bifurcation, 95-Trial / 77-Lesson Ledger & Full-Peer Co-op Convergence

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Antigravity `L0–L13` Harness, Quantitative Falsification (`L8`/`L13`) & Dual-Machine 18-Repo Co-op (`H0–H7` × `T1–T5`)
- **Evidence Grade:** E4 (`26` ADRs, `13/13` AGY Probes, `21/21` Pytest, `95` Pre-Registered HLZ Trials `t*(96) = 4.1882` & `77` Compiled `E1–E4` Lessons)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/meridian, https://github.com/native-agent-stack/sota-compounding-lab
- **Revisit Trigger:** 2027-01-02 or pre-registered Trial `#96` (`t*(96) = 4.1882`)

## Context and Problem Statement

Following `v3.9.5`–`v3.9.6` (`46/46` SOTA skill convergence, `17/17` workflows, `Noesis` 4K primary TradingView CTA/UTP session guard, and `H094`'s `-97.274 bps` pure-passive runaway-breakout finding), the ecosystem required empirical execution of pre-registered Trial `#95` (`H095_TWO_STAGE_LIT_QUEUE_15S_TO_10BPS_MARKETABLE_COLLAR_ORB_CPCV`, `spec_sha256 = 5abe51a4caacf4bf6955a331b495310fae1791a8d74a76c111bc9e6a35b5f4fa`) and zero-overlap co-op ADR alignment across all `18` active repositories and `3` execution surfaces (`Mac M5 Max`, `Stationary Noesis Win32`, `* Noesis-Carbon` WSL2 `ext4`).

## Decision Outcome

1. **Codify `H095` Stage-1 vs Stage-2 Microstructure Bifurcation (`E4` Lesson `8984c339ec706f4f`):**
   - Across `319` shielded ORB ignitions (`<= 2026-10-15`, `700` `XNYS` sessions), Stage-1 `[0..15s]` immediate passive L1 bid fills (`n = 134`, `80/134 = 59.7%` `trade_through`) earned `-8.736 bps` net `1x` (`-14.108 bps` `2x`) due to false-breakout seller sweeps, whereas Stage-2 `+15s` bid-survived `<= 10.0 bps` marketable ask collars (`n = 55`) earned `+20.779 bps` gross / `+15.305 bps` net `1x` / `+9.832 bps` net `2x` (`+47.804 bps` adverse-selection improvement vs `H094`, `8/15` disjoint CPCV `> 0`).
   - Combined `189`-fill cohort (`-1.740 bps` net `1x`, `t = -0.1089 < 4.1858`) is honestly recorded as `FAILED` on `ALPHA_STRATEGY_MINOR`, advancing the cumulative HLZ hurdle to `t*(96) = 4.1882` and promoting protective `<= 10.0 bps` collar & `15s` sweep-toxicity guards on `PROTECTIVE_FILTER_OR_GOVERNANCE` (`v3.9.7`).
2. **Maintain `26` GitHub-Evidenced MADR 4.0 ADRs & `46`-Skill / `7`-DAG AGY Parity:**
   - Synchronize `SOTA_HARNESS_MANIFEST.json` (`26` ADRs) with `sota-harness-foundation` `ADR-0033`, `meridian` `0062`, `sota-compounding-lab` `ADR-0013`, and `sota-multi-model-workflows` `ADR-0019`.

## Alternatives Considered

- **Suppressing negative combined `H095` trial metrics while promoting Stage-2 `+15s` collar alpha:** Rejected; violates Harvey–Liu–Zhu familywise accounting and `sota-quant-research-protocol` Gate 7.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` -> `26 GitHub-evidenced ADRs valid, 0 drift`
- `python3 harness/run_probes.py` -> `13/13 probes PASSED`
- `pytest -q && python3 scripts/merge_gate.py && gitleaks git --staged --no-banner` -> `21 passed`, `[AGY-MERGE-GATE PASS]`, `0` leaks
