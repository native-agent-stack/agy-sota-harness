# ADR-0012: L11–L12 18-Repo Read-Only Trading Shelf, On-Demand Computer Use & `SkillOpt` 6-Subagent Evolution

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `L11` Trading Upstream Shelf / Computer Use & `L12` Self-Evolution
- **Evidence Grade:** E4 (`18/18` Clean Clones, `6` Subagents & Redacted Trajectory Mining Verified)
- **GitHub Evidence:** https://github.com/alpacahq/alpaca-py (`c42add7c0a7026e2ead3ed64e76f4def2b99fda4`), https://github.com/nautechsystems/nautilus_trader (`da6b57aefdd62b44f675e434ffcfefca7f4025dd`), https://github.com/pola-rs/polars (`7f902bd3ffd27ff82d14278a09a295ff2f7aed92`), https://github.com/duckdb/duckdb (`d54cbbe3df17e8e5ce68312f483b4155836112aa`), https://github.com/dgunning/edgartools (`574c2bd15f6c629bceef03b6550ea8ac8abf3473`), https://github.com/nkaz001/hftbacktest (`5f3ec40b2afb764e0fea112f941ed85523ef4e88`), https://github.com/vercel-labs/agent-desktop (`1.3.1`), https://github.com/microsoft/SkillOpt (`2026-SOTA`)
- **Revisit Trigger:** 2027-01-01 or owner-approved `PINS.md` / `upstream-map.toml` commit bump

## Context and Problem Statement

LLM training cutoffs trail rapidly evolving trading libraries (`alpaca-py`, `nautilus_trader`, `polars`, `duckdb`, `edgartools`, `ml4t-diagnostic`, `skfolio`, `hftbacktest`, `ib_async`, `perspective`, `lightweight-charts`, `quantstats`, `vectorbt`, `pandera`, `exchange_calendars`, `statsmodels`), while recurring trajectory friction (`transcript.jsonl` tool retries and truncations) goes unaddressed without a structured self-evolution loop.

## Decision Outcome

1. **18-Repo Immutable Reference Shelf (`~/Documents/upstream/`):** Pin all 18 trading and statistical upstreams by exact 40-character Git commit SHA in `upstream-map.toml`, verify `18/18` clean `git status` in `merge_gate.py` and `probe_l11`, and forbid writes via `PreToolUse` + Seatbelt.
2. **On-Demand Computer Use (`agent-desktop@1.3.1` & `agent-browser@0.43.0`):** Use macOS Accessibility (`AXUIElement`) strictly for discrete user-requested chart symbol focus or preset setup in `TradingView.app`, never continuous GUI polling.
3. **6 Specialist Subagents & `SkillOpt` Evolution (`sota_trajectory_friction`):** Provide `sota-rd-proposer`, `sota-falsifier`, `sota-code-verifier`, `sota-deep-synthesizer`, `sota-skillopt-curator`, and `sota-subsession-orchestrator` across AGY and `~/.claude/agents/`, mining redacted `transcript.jsonl` logs to propose validation-gated `SKILL.md` and hook upgrades.

## Alternatives Considered

1. **Relying on model training memory or unpinned web snippets for broker/backtest APIs:** Rejected — causes subtle signature mismatches (e.g., inventing nonexistent `ExitGate` symbols in `nautilus_trader`).
2. **Unvalidated automatic self-editing of `GEMINI.md` after every session:** Rejected — causes prompt bloat; `SkillOpt` requires empirical `run_probes.py` + `sota-doctor` validation gates.

## Verification Witness

- `harness/run_probes.py` `L11` & `L12` verify `18/18` clean SHA-pinned upstream clones, `sota_ecosystem_convergence`, and `sota_trajectory_friction`.
- `~/.agents/bin/sota-doctor` `L1`, `L2`, and `L6` verify `6` AGY subagents, `6` Claude subagents, and `18` clean upstream clones.
