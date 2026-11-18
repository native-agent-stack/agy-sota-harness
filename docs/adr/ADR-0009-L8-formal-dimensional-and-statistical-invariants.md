# ADR-0009: L8 Formal Dimensional, NMS Tick-Grid (`ADR-0022 <= 2.00%`), `Pandera` & `Hypothesis` Invariants

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `L8` Formal Correctness, Property Fuzzing & Structural AST Rules
- **Evidence Grade:** E4 (Property-Tested Across IEEE-754 Edge Cases & AST-Grep Audited)
- **GitHub Evidence:** https://github.com/trailofbits/skills (`149d7b21f4067765b82e67029730b42d228ef4b4`), https://github.com/HypothesisWorks/hypothesis (`6.170.15`), https://github.com/unionai-oss/pandera (`02b375ab43f39f8c5c5108695c1791fa04f99a26`), https://github.com/skfolio/skfolio (`90e3fb907fab39d244d899f3caf4e9676889309c`), https://github.com/ml4t/diagnostic (`19e76072e64a18c9ba56130e4a7bcc0bc871f57e`)
- **Revisit Trigger:** 2027-01-01 or Reg NMS sub-dollar / half-penny tick-increment rule changes

## Context and Problem Statement

Quantitative execution and factor code is vulnerable to silent `100x` unit confusion (`bps` vs `pct` vs decimal ratio), IEEE-754 floating-point tick-rounding overshoot above the hard `2.00%` `ADR-0022` protective stop ceiling, `NaN`/`Inf` propagation, naive timezone-unaware `datetime.now()`, and unclustered OLS `t`-statistics.

## Decision Outcome

1. **Exact `Decimal` NMS Tick-Grid & Dimensional Types (`src/agy_sota/invariants.py`):** Enforce explicit dimensional wrappers (`bps`, `pct`, `ratio`), `Decimal` Reg NMS tick-grid stop quantization (`$0.01` for `>= $1.00`, `$0.0001` sub-dollar) strictly `<= 2.00%` of entry price, `<= 2026-10-15` pre-wall bounds, canonical Harvey–Liu–Zhu `t*(N)`, and `Pandera` Polars OHLCV schemas (`high >= max(open, close, low)`, finite positive prices).
2. **`Hypothesis` Fuzzing & 4 `ast-grep` Structural Rules (`rules/ast-grep/sgconfig.yml`):** Fuzz invariants with `Hypothesis@6.170.15` and scan repositories deterministically via `sota_ast_lint_audit` (`no-live-alpaca-trading-import`, `no-live-ibkr-port`, `no-naive-datetime-now`, `no-unclustered-ols-fit`).

## Alternatives Considered

1. **Binary float `round(price * 0.98, 2)` stop calculation:** Rejected — IEEE-754 representation rounding can exceed `2.00%` risk on cent boundaries (`$250,000.49` witness).
2. **Regex-only static checks instead of `ast-grep`:** Rejected — regexes miss multiline imports and produce false positives in comments/strings.

## Verification Witness

- `harness/run_probes.py` `L8` verifies all `4` `ast-grep` YAML rules catch intentional synthetic violations and pass `src/` with `0` findings.
- `mise exec -- uv run pytest` runs `Hypothesis` property suites across `tests/test_agy_sota_ecosystem.py` (`PASS`).
