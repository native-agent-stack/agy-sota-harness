# ADR-0011: L10 Scoped Scheduled Sidecars, Zero-Telemetry `agentsview` & macOS TCC-Safe `24/5` Dead-Man Watchdog

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `L10` Observability, Sidecars & `24/5` Daemon Supervision
- **Evidence Grade:** E4 (`35` Scoped Grants + Live `60s` `launchd` Dead-Man Alert & Recovery Verified)
- **GitHub Evidence:** https://github.com/kenn-io/agentsview (`0.47.0`), https://github.com/google-antigravity/antigravity-sdk-python (`agy@1.5.3`), https://github.com/native-agent-stack/sota-dynamic-trail-c (`584f22b4dba65819c538734a5f2bdf569c900566`)
- **Revisit Trigger:** 2027-01-01 or macOS `launchd` TCC folder-protection policy change

## Context and Problem Statement

Unattended `24/5` paper execution (`:8787` `sota-mover-ranker` and `:8799` `sota-dynamic-trail-c`) faces two OS-level failure modes on macOS: (1) aggressive idle sleep (`pmset sleep=1`) suspending WebSocket/SSE loops unless `/usr/bin/caffeinate -dimsu` is held, and (2) macOS TCC blocking non-FDA `launchd` `/bin/bash` jobs from reading `~/Documents/*` (`Operation not permitted` -> `exit 78` crash loops).

## Decision Outcome

1. **TCC-Safe `launchd` Placement & `/usr/bin/caffeinate -dimsu` Wrapping:** Run `launchd`-supervised `24/5` daemons and watchdogs from non-TCC `$HOME` paths (`~/sota-dynamic-trail-c` for `com.sota.dynamic-trail-c` and `~/.agents/bin/sota-deadman-check` for `com.sota.24x5-deadman-watch`), wrapping active daemons in `/usr/bin/caffeinate -dimsu` while keeping `~/Documents/sota-mover-ranker` `RunAtLoad=false` unless FDA is granted (launching `:8787` from TCC-authorized sessions).
2. **60-Second Dead-Man Watchdog (`com.sota.24x5-deadman-watch`):** Probe `:8787` HTTP, `:8799` HTTP, `caffeinate -dimsu` process presence, and `launchctl` `exit-78` absence every `60s`, writing `~/.agents/bus/deadman_status.json` and pushing deduplicated alerts to macOS Notification Center and `peer_bus.db`.
3. **Scoped AGY Sidecar & Local `agentsview`:** Bind `sota-early-mover-paper-goal` (`*/20` market hours) to `35` explicit `access_grants` and keep `agentsview@0.47.0` strictly local (`AGENTSVIEW_TELEMETRY_ENABLED=0`).

## Alternatives Considered

1. **Running `launchd` `KeepAlive=true` `/bin/bash` wrappers directly inside `~/Documents/`:** Rejected — empirically triggered `6,218` `exit 78` (`EPERM`) crash loops in `daemon.err.log`.
2. **Disabling macOS TCC or modifying system SIP settings:** Rejected — violates host security boundaries; non-TCC `$HOME` runtime paths solve the root cause cleanly.

## Verification Witness

- `harness/run_probes.py` `L10` verifies `sidecar.json` and `35` scoped `access_grants`.
- `~/.agents/bin/sota-doctor` `L9` verifies all `3` LaunchAgent plists, `caffeinate -dimsu`, and live `sota-deadman-check` execution (`0` `exit-78` loops).
