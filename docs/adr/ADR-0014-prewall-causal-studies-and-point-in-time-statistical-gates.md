# ADR-0014: Pre-Wall (`<= 2026-10-15`) Causal Microstructure Studies & Point-in-Time Statistical Promotion Gates

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `T1–T6` Quantitative Research Protocol & Adversarial Falsification (`Q1–Q4`)
- **Evidence Grade:** E4 (`sota-falsifier` Red-Team Survived `P0=0..P3=0`, `15/15` + `38/38` `pytest` Verified)
- **GitHub Evidence:** https://github.com/statsmodels/statsmodels (`278ff9950636cdd4939b4055e339a8e681d79cab`), https://github.com/skfolio/skfolio (`90e3fb907fab39d244d899f3caf4e9676889309c`), https://github.com/ml4t/diagnostic (`19e76072e64a18c9ba56130e4a7bcc0bc871f57e`), https://github.com/dgunning/edgartools (`574c2bd15f6c629bceef03b6550ea8ac8abf3473`), https://github.com/nkaz001/hftbacktest (`5f3ec40b2afb764e0fea112f941ed85523ef4e88`), https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-mover-ranker (`bb1d90b10a95333975ced7e4d16c59d5e67f5e94`)
- **Revisit Trigger:** 2027-01-01 or owner-authorized study-wall advancement beyond `2026-10-15`

## Context and Problem Statement

Two-round adversarial red-teaming (`sota-falsifier` + `sota-code-verifier`) across pre-wall factor discovery and live paper compounding uncovered subtle leakage and multiple-testing failure modes: (1) post-wall FINRA short-volume (`20261113 > 20261015`) and post-wall `latest_scan` symbols leaking into `<= 2026-10-15` historical panels, (2) split-adjusted `Adjustment.SPLIT` bars inflating reverse-split penny stocks past nominal `$2.00` / `$2M` gates, (3) overlapping 3-session returns inducing $MA(2)$ serial correlation ($\rho_1 \approx 2/3, \rho_2 \approx 1/3$) and unpurged Train/OOS boundary leakage, (4) understated HLZ hurdles (`3.30` vs canonical `4.14` at $N \ge 77$) and `status()` overwriting `dsr_merit_gate`, (5) premature online strategy threshold mutations on `n_closed = 2..3` trades, and (6) CTA/UTP trade condition `'I'` (Odd Lot) vs `'F'` (Intermarket Sweep Order) confusion on nanosecond tick tapes.

## Decision Outcome

1. **Strict Pre-Wall (`<= 2026-10-15`) & Point-in-Time `asof` Joins (`prewall_study.py`, `intraday_prewall_study.py`, `tick_orb_prewall_study.py`, `multifeed_lake.py`):**
   - Enforce `trade_date <= 2026-10-15`, causal `asof` SEC `424B5`/`S-3` dilution shields (`edgartools` / Polars `join_asof`), causal `short_vol_asof(sym, day0)` (`d_tag <= 20261015` and `<= day0`), CTA/UTP `'F'`-ISO vs `'I'`-Odd-Lot condition codes + `BJZZ` (`x == 'D'`) sub-penny dark-pool classification, and zero post-wall `latest_scan` universe seeding.
2. **Fail-Closed `Adjustment.RAW` Filters, `[t-1..t+3]` Split Drop & Next-Open `o1` Execution:**
   - Apply nominal `$2.00` price and `$2,000,000` 20-day dollar-volume filters strictly on fail-closed `Adjustment.RAW` bars, drop events straddling split ex-dates anywhere in `[t-1..t+3]` (including `t0`), anchor forward returns at executable next-session open `o1` (or firm NBBO ask `ap_entry` on tick studies), and require positive net returns after `2x` round-trip costs (`16 bps`).
3. **Canonical HLZ `t*(N)`, Purged `CPCV`, $MA(2)$ Hansen–Hodrick `DSR` & Empirical-Bayes Credibility (`N >= 81`):**
   - Backfill all historical pre-wall trials into `~/.agents/wiki/HYPOTHESIS_LEDGER.md` (`N = 81`, canonical `NormalDist().inv_cdf(1 - 0.00135 / N)` $= 4.1494$), purge `3` sessions at Train/OOS boundaries, run `skfolio` `CombinatorialPurgedCV(purged_size=3, embargo_size=2)` on daily Top-5 cohorts, deflate overlapping 3-day Sharpe via Hansen–Hodrick `1 / sqrt(1 + 2*max(0, rho1) + 2*max(0, rho2))`, and lock online threshold tightening below `prior_n = 4` closed trades (`tp_r_mult` locked until `n_closed >= 30`).

## Alternatives Considered

1. **Falling back to `Adjustment.SPLIT` when `Adjustment.RAW` errors:** Rejected — silently re-admits reverse-split penny stocks (`RSPLT` counter-proof).
2. **Approximating HLZ via `sqrt(2 * ln(N)) + 0.35`:** Rejected — understates canonical `NormalDist().inv_cdf(1 - 0.00135 / N)` by `-0.84` at $N=77$.

## Verification Witness

- `agy-sota-harness`: `pytest` `15/15` (`tests/test_agy_sota_ecosystem.py` + `tests/test_tick_orb_prewall.py` PASS).
- `sota-mover-ranker`: `pytest` `38/38` (`test_q1_q4_and_falsifier_p0_p3_invariants` PASS); `sota-falsifier` (`P0=0..P3=0`) and `sota-code-verifier` (`P0=0..P3=0`) signed off.
