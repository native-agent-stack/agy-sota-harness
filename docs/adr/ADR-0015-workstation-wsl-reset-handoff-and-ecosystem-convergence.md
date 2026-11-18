# ADR-0015: Workstation WSL-Reset Handoff, Shared-VM Isolation & 22-Repository Ecosystem ADR Convergence

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** `L0–L12` × `T0–T8` Dual-Machine Orca Mesh & Organization Convergence
- **Evidence Grade:** E4 (`sota-doctor` `11/11`, `sota-org-doctor --live` `22/22`, `run_probes.py` `13/13`, `pytest` `16/16` Verified)
- **GitHub Evidence:** https://github.com/stablyai/orca, https://github.com/native-agent-stack/native-agent-stack, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/meridian, https://github.com/gitleaks/gitleaks
- **Revisit Trigger:** 2027-02-16 or post-reset WSL2 `meridian` distribution re-import on `Noesis`

## Context and Problem Statement

Ahead of the stationary workstation (`Noesis`, `100.110.115.22`, `64` logical cores, `128 GB` RAM, RTX 4090) WSL2 reset (`meridian` `ADR-0055` & `ADR-0056`), the retiring workstation leads delivered formal handoffs across `meridian` (`54` ADRs including `ADR-0053` gateway rules, PRs `#6`, `#7`, `#8`), `sota-private-vault` (`ADR-0007`, `2,084` scrubbed owner directives), and `tsl` (`ADR-0018`, ungated paper path with `live` closed), naming native Gemini 4 Carbon (`agy-sota-harness`) as the primary successor foundation alongside portable Apple M5 Max (`64 GB` RAM) and paired `Noesis` Orca execution.

## Decision Outcome

1. **Dual-Machine Orca Lane & Shared-VM WSL2 Non-Interference (`~/.agents/bin/sota-workstation`, `sota-doctor` `L10`, `ADR-0021`):**
   - Mirror all `18` active `native-agent-stack` repositories under `C:/sota-workstation/*` on `Noesis` (`Orca v1.4.261`) paired with the portable Apple M5 Max (`Orca v1.4.255`), with autonomous offline M5 Max failover (`14` threads AC / `8` battery / `4` `<35%` conservation) and single-active-broker-host isolation (`singleActiveBrokerHostOnly = true`).
   - Hard-refuse `wsl --shutdown` and any mutation of co-resident `sextant`, drive `D:`, or recovery drive `Z:` inside the shared WSL2 VM; hard-refuse unauthenticated Tailscale Serve proxying of loopback model gateways (`:20128`) and pairing `ANTHROPIC_BASE_URL` with `CLAUDE_CODE_OAUTH_TOKEN`.
2. **Full 22-Repository `native-agent-stack` Successor Convergence:**
   - Synchronize `SOTA_ECOSYSTEM_MANIFEST.json` (`v3.2.0` / `3.0.0` schema) across all `18` active repositories (`9 PUBLIC` unlimited GitHub Actions + `9 PRIVATE` zero-Actions-burn active repos) plus `4 PRIVATE` cold-archived seals, enforcing `100%` paper-only autonomous execution (`PA...` `<= 200` req/min, `DU... :4002` `<= 3,000` msg/min, `ADR-0022 <= 2.00%` protective stops) and digest-only private vault retrieval.

## Alternatives Considered

1. **Wait for manual WSL2 re-provisioning before landing ecosystem ADRs:** Rejected — landing all `18` active repos onto `C:/sota-workstation/*` and GitHub `native-agent-stack` ensures zero downtime and instant clone/mount readiness after the WSL2 distro reset.
2. **Allow `wsl --shutdown` from automated cleanup scripts:** Rejected — terminates co-resident `sextant` workloads sharing the WSL2 VM.

## Verification Witness

- `python3 harness/run_probes.py` -> `13/13 PASS`
- `python3 scripts/merge_gate.py` -> `PASS`
- `pytest -q` -> `16/16 PASS`
