# ADR-0033: `v3.10.7` Antigravity Hybrid 5-Layer Computer-Use Escalation & Zero-Friction Permission Tiering

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Antigravity `L0–L13` Harness, Hybrid Computer-Use Routing (`L1–L4`), & Tiered Gated-Action Governance (`H1–H3`)
- **Evidence Grade:** E4 (`33` GitHub-Evidenced ADRs, `10/10` Schema-Typed AGY `run_workflow` DAGs, `13/13` Live Harness Probes, `sota-harness-foundation@e3e8d9cf` `ADR-0042` Contract, `pytest` & `merge_gate.py` `0` Leaks Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/simular-ai/Agent-S, https://github.com/trycua/cua, https://github.com/microsoft/UFO, https://github.com/vercel-labs/agent-browser, https://github.com/HKUDS/CLI-Anything, https://github.com/steipete/peekaboo, https://github.com/mediar-ai/terminator
- **Revisit Trigger:** `2026-12-06` `23/5` Consolidated SIP cutover or Antigravity browser/UIA runtime upgrade

## Context and Problem Statement

Antigravity (`agy`) orchestrates workflows across `Portable Mac M5 Max` and `Stationary Noesis` (`100.110.115.22`), spanning CLI tools, `:8792` Zero-Terminal RPC, MCP servers, embedded/web browsers, and desktop UI toggles (`orca computer`). Pure GUI screenshot loops introduce latency, focus stealing, and token overhead, while ambiguous permission boundaries slow owner-sanctioned configuration updates without protecting hard trading/security invariants.

## Decision Outcome

1. **Adopt the 5-Layer Hybrid Computer-Use Escalation Ladder (`ADR-0042` / `sota-harness-foundation`):**
   - **Layer 1 (Default):** Programmatic CLI, `:8792` Zero-Terminal RPC (`sota-workstation`), `sota-bus`, `hcom`, and `CLI-Anything` / MCP tools (`0` pixel tax).
   - **Layer 2 (Native Desktop UI):** Semantic OS accessibility (`orca computer` background mode on `darwin`, UIA on `win32`, `steipete/peekaboo`, `mediar-ai/terminator`, `trycua/cua`, `microsoft/UFO`).
   - **Layer 3 (Web UIs):** Compact browser CDP accessibility refs (`vercel-labs/agent-browser`, `@playwright/cli`, `orca browser`, `browser` subagent).
   - **Layer 4 (`Agent-S` S4 Distillation & VLM Fallback):** Visual pixel CUA only when UI surfaces are unexposed; recurring GUI workflows are distilled into deterministic CLI/config scripts.
2. **Enforce Three-Tier Gated-Action Governance Alongside Intact `L1` Guards:**
   - **`OWNER_ZERO_FRICTION_SEAMLESS`:** Owner-sanctioned non-destructive Orca, multi-runtime, harness, and paper operations execute seamlessly via documented native configs/CLIs/RPC/UIA.
   - **`EXPLICIT_HUMAN_TRUST_GATE`:** Platform trust clicks (e.g., Orca `97bd1f5e` hooks trust prompt), OS TCC/admin elevation, CAPTCHAs, and unclassified actions are surfaced cleanly to the owner for 1-click decision.
   - **`FAIL_CLOSED_HARD_INVARIANT`:** Preserves `harness/run_probes.py` `probe_l1()` intact — Stage-5 live endpoints (`~/.claude/bin/live`, `api.alpaca.markets`, `:4001`/`:7496`/`:8798`) enforce gated `decision in ("ask", "deny")` and immutable `~/Documents/upstream/` shelf mutation remains strictly `deny`.

## Alternatives Considered

- **Routing Desktop & Browser Tasks Primarily Through Visual Screenshots:** Rejected — slower, focus-disruptive, and higher failure rate than semantic accessibility, compact CDP refs, and CLI/RPC.
- **Weakening `L1` `PreToolUse` Probes for Convenience:** Rejected — breaks Stage-5 Lossless live-capital and immutable-shelf protections.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` (`33 GitHub-evidenced ADRs valid, 0 drift`)
- `python3 scripts/merge_gate.py && python3 harness/run_probes.py && pytest -q && ruff check . && gitleaks detect --source . --no-git --no-banner` (`AGY-MERGE-GATE PASS`, `0` leaks)
