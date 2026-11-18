# ADR-0023: v3.9.1 Twin Overnight Stop-Whipsaw Shield (`H092`+`H093`), MCP Stdio Non-Blocking Reliability & 93-Trial / 69-Lesson Convergence

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Antigravity `L0–L13` Harness, MCP Reliability & Pre-Wall Microstructure (`H2` / `H4` × `T1–T5`)
- **Evidence Grade:** E4 (`13/13` AGY Probes, `23` ADRs, `93` HLZ Trials, `69` `E1–E4` Lessons & `21/21` Pytest Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-mover-ranker, https://github.com/native-agent-stack/sota-compounding-lab, https://github.com/stablyai/orca
- **Revisit Trigger:** 2027-01-02

## Context and Problem Statement

Following `ADR-0022` (`v3.9.0` 9-Feed `DF1..DF9` & Orca Lane Hubs v2), pre-registered Trials `#92` (`H092`, `5,400` events) and `#93` (`H093`, `2,073` events) plus live `:8787` MCP/E2E telemetry (`Lesson c85fbef3665b71bd`) established two operational invariants for `v3.9.1`:
1. Unconditional `MOC -> MOO` overnight holds on high-sigma equities suffer `18.8%–23.1%` extended-hours `-200 bps` thin-bar stop whipsaw prior to `09:30` ET (`t = -5.4145` & `-4.6903`), advancing the HLZ ledger to `N = 93` (`t*(94) = 4.1834`) and `69` `E1–E4` lessons.
2. MCP stdio child processes (`L3`) must never pair unread `stderr=PIPE` with blocking `stdout.readline()` across `>64 KB` diagnostic bursts, and `:8787` E2E execution enforces `ADR-0017` tight-spread/streak shields plus 1-share dust-crumb rejection (`sota-mover-ranker @ e8eebd7a0570`).

## Decision Outcome

1. **Advance `SOTA_ECOSYSTEM_MANIFEST.json` to `manifestVersion = "3.9.1"` (`23` ADRs):**
   - Align `agy-sota-harness` (`L0–L13`) with `sota-multi-model-workflows` `v3.9.1` (`ADR-0017`), `canon` `0180` (`18/18` `UPSTREAM.md`), and `.github` `v3.9.1` (`ADR-0017`).

## Alternatives Considered

- **Leaving `manifestVersion` at `3.9.0`:** Rejected; full-landscape `v3.9.1` locks identical SemVer across workflow, harness, umbrella, and org manifests.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` -> `23 GitHub-evidenced ADRs valid, 0 drift`
- `pytest -q` -> `21 passed`
- `python3 scripts/merge_gate.py && gitleaks git --staged --no-banner` -> `[AGY-MERGE-GATE PASS]`, `0` leaks
