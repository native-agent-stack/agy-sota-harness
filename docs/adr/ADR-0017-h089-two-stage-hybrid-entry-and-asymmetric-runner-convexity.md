# ADR-0017: Pre-Registered Trial #89 (`H089`) Two-Stage Hybrid Entry × 50/50 Asymmetric Runner Convexity & 5-Trial ORB Execution Synthesis

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Quantitative Microstructure, Execution Physics & Multi-Trial Statistical Gates (`T1–T4` × `L8` × `P0–P5`)
- **Evidence Grade:** E4 (Runtime-Verified Across `14,750` Pre-Wall Nanosecond SIP Pairs, `587` Dates `<= 2026-10-15`, `sota-bus` `Trial #89` & `Hypothesis` Property Suite)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-harness-foundation (`c8dcebe052d1d7baf9e54cadf7ab651e5c0d9cc4`), https://github.com/nkaz001/hftbacktest (`5f3ec40b2afb764e0fea112f941ed85523ef4e88`), https://github.com/nautechsystems/nautilus_trader (`da6b57aefdd62b44f675e434ffcfefca7f4025dd`), https://github.com/ml4t/diagnostic (`19e76072e64a18c9ba56130e4a7bcc0bc871f57e`), https://github.com/skfolio/skfolio (`90e3fb907fab39d244d899f3caf4e9676889309c`), https://github.com/dgunning/edgartools (`574c2bd15f6c629bceef03b6550ea8ac8abf3473`)
- **Revisit Trigger:** Pre-registered Trial `N >= 90` (`t*(90) >= 4.1734`), `PostWallCohortLedger` reaching `N >= 250` real Paper round-trips, or `2026-12-06` `23/5` SIP cutover

## Context and Problem Statement

`Trial #88` (`H088`, `sota-harness-foundation` `ADR-0024`) proved that pairing `hftbacktest::RiskAdverseQueueModel` (`bs * 100.0` shares) with a single-tranche `+60 bps` Gain-Lock / `84.8 bps` `1m` trail reduced `CVaR_95` by `-44.55%` (`-724.6 -> -401.8 bps`) and `SE` by `-15.17%`, but suffered two structural drags:
1. **Unfilled Runaway Exclusion (`-46.37 bps`):** Waiting for full `USD 25,000` passive queue depletion missed `13.17%` of immediate breakout runaways.
2. **Single-Tranche Right-Tail Skewness Censoring (`97.8%` early exit):** Only `2.20%` (`28 / 1,273`) of positions survived to `15:55` ET RTH close.

We pre-registered `Trial #89` (`H089_TWO_STAGE_HYBRID_ENTRY_X_ASYMMETRIC_RUNNER_CONVEXITY`, `spec_sha256 = 0dffdb5d97cd5ef8d8964887d3b7f93f32fc6052540d36b081db79b2f5f09447`, `t*(89) = 4.1709`) in `src/agy_sota/hybrid_runner_prewall_study.py` to evaluate Two-Stage Hybrid Entry (`50%` passive bid in `120s` + `50%` full passive queue in `180s` or `120s` runaway ask join) paired with `50/50` Core Gain-Lock (`+150 bps`, `65%` MFE) + Uncapped `15:55` ET Breakeven-Runner (`+10 bps` BE @ `+180 bps`) under an `ADVERSE_STOP_FIRST` `180 bps` (`ADR-0022`) initial stop.

## Decision Outcome

1. **Empirical `H089` Findings (`2024-02-01 .. 2026-10-15`, `1,529` Participated Events Across `587` Dates):**
   - **Runaway Participation & Right-Tail Survival Restored:** Participation climbed from `86.83%` to **`95.50%`** (`1,378` `passive_100pct` + **`151` `runaway_join_50pct`**), and `15:55` ET Runner survival jumped **`23x`** from `2.20%` to **`50.75%`** (`776 / 1,529`).
   - **Monotonic Expectancy & Variance Improvement Over `H088`:** Net `1x` excess return improved **`+6.195 bps`** overall (`-15.160 -> -8.965 bps`) and **`+22.725 bps` in the 2026 subperiod** (`-28.500 -> -5.775 bps`), while date-clustered `SE` compressed an additional **`-19.19%`** (`6.915 -> 5.588 bps`, **`-42.4%` total SE reduction** vs `H085` `9.70 bps`).
   - **Final Isolated Bottleneck (`Kaminski & Lo 2014` High-Sigma V-Shakeout):** `49.25%` (`753 / 1,529`) of volatile ORB movers touched the fixed `-180 bps` intrabar hard stop during V-bottom shakeouts (`t = -1.6044 < 4.1709`; honestly recorded as `FAILED` on `sota-bus`).
2. **Architectural Synthesis Applied to Live Paper Execution (`sota-mover-ranker` `:8787`):**
   - Split into `50/50` Core-Harvest + Zero-Loss Runner Convexity **strictly after** green Gain-Lock arming (`+8 bps` breakeven+ floor on the `50%` Runner, uncapped up to `+125 bps` before progressive MFE retention), capturing `H089`'s `23x` right-tail runner expansion without `100%` micro-Gain-Lock censoring.

## Alternatives Considered

1. **Evaluating `H089` only on `2026` (`-5.78 bps` vs `-28.50 bps`) or trimming V-shakeout dates post-hoc:** Rejected — violates `sota-quant-research-protocol` full pre-wall (`2024–2026 <= 2026-10-15`) sample integrity and HLZ multiplicity accounting.
2. **Keeping `100%` single-tranche `+16..+22 bps` Gain-Lock on multi-share live paper movers:** Rejected — empirically proven in both `H088` (`97.8%` early censoring) and `:8787` (`283` RTs averaging `+12.6 bps` = `+0.11R` vs `+140.2 bps` = `+1.02R` on Dynamic Trail Winner Locks) to starve right-tail payoff asymmetry.

## Verification Witness

- `python3 scripts/architecture_catalog.py --check` -> `17 GitHub-evidenced ADRs valid, 0 drift`
- `python3 scripts/merge_gate.py` -> `[AGY-MERGE-GATE PASS]`
- `python3 harness/run_probes.py` -> `13/13 probes PASSED`
- `pytest -q` (including `tests/test_hybrid_runner_prewall.py` `Hypothesis` invariants), `ruff`, `ty@0.0.104`, `ast-grep`, and `gitleaks` -> `100% PASS`
