# ADR-0010: L9 OS-Level Seatbelt Kernel Confinement, `.gitleaks.toml` & Fail-Closed `merge_gate.py`

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `L9` OS Sandbox, Secret Firewall & Repository Privacy Gate
- **Evidence Grade:** E4 (Seatbelt Policy, `gitleaks` & Dual-Repo Merge Gates Verified)
- **GitHub Evidence:** https://github.com/anthropic-experimental/sandbox-runtime (`0.0.83`), https://github.com/gitleaks/gitleaks (`8.30.1`), https://github.com/native-agent-stack/agy-sota-harness
- **Revisit Trigger:** 2027-01-01 or macOS Seatbelt / `sandbox-runtime` policy schema change

## Context and Problem Statement

Application-layer hooks alone do not confine child subprocesses spawned inside complex shell pipelines, and tracked repository commits must never leak `PA...`/`DU...` paper account IDs, `AK...`/`PK...` API keys, raw dollar balances, personal email addresses, or hardcoded `/Users/<user>/` workstation paths.

## Decision Outcome

1. **OS Kernel Policy (`policies/srt-agy-worker.json`):** Configure `@anthropic-ai/sandbox-runtime@0.0.83` to deny network egress to `api.alpaca.markets`, deny reads of `~/.ssh` and `~/Library/Keychains`, and deny writes to `~/Documents/upstream`.
2. **Layered Secret & Path Gate (`.gitleaks.toml` + `.githooks/pre-commit` + `scripts/merge_gate.py`):** Block secrets, `PA...`/`DU...` account IDs, hardcoded local home paths, unmapped files in `upstream-map.toml`, dirty/drifted `~/Documents/upstream/` clones, ADR catalog drift, and non-`noreply` Git commit emails fail-closed before commit or merge.

## Alternatives Considered

1. **Manual code review for path/account-ID redaction:** Rejected — error-prone across fast multi-agent iterations; regex + `gitleaks` tripwires in `merge_gate.py` catch leaks deterministically in `<2s`.
2. **Allowing personal git author emails in private repos:** Rejected — enforcing `users.noreply.github.com` everywhere prevents accidental PII exposure if visibility ever changes.

## Verification Witness

- `harness/run_probes.py` `L9` verifies `policies/srt-agy-worker.json`, `.gitleaks.toml`, `agy-sota-harness/scripts/merge_gate.py`, and `sota-mover-ranker/scripts/merge_gate.py` (`PASS`).
