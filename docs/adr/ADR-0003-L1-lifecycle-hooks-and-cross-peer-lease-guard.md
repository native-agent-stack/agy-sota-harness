# ADR-0003: L1 Fail-Closed Lifecycle Hooks, Live-Capital Firewall & SQLite Peer-Lease Guard

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `L1` Lifecycle Hooks & Multi-Peer Safety
- **Evidence Grade:** E4 (Adversarial Hook Payloads & System Python `3.9` Verified)
- **GitHub Evidence:** https://github.com/google-antigravity/antigravity-sdk-python (`agy@1.5.3`), https://github.com/gitleaks/gitleaks (`8.30.1`), https://github.com/aannoo/hcom (`v0.7.31`), https://github.com/native-agent-stack/agy-sota-harness
- **Revisit Trigger:** 2027-01-01 or any broker endpoint, hook event schema, or macOS system Python change

## Context and Problem Statement

Under high-autonomy (`Turbo Mode`) execution across concurrent Antigravity, Claude Code, and Codex sessions, three hazards must be intercepted deterministically below model weights: (1) accidental calls to live real-money broker endpoints (`api.alpaca.markets`, `.claude/bin/live`, IBKR ports `4001`/`7496`) or writes into `~/Documents/upstream/`, (2) uncoordinated concurrent edits to files leased by an active peer session, and (3) macOS `/usr/bin/python3` (`3.9.6`) hook crashes from Python `3.11+`-only stdlib imports (`datetime.UTC`).

## Decision Outcome

1. **Hard-Deny `PreToolUse` Firewall (`pre_tool_guard.py` & `peer_hook_adapter.py`):** Block `.claude/bin/{live,alpaca-live-mcp,key-store}`, `api.alpaca.markets`, IBKR ports `4001`/`7496`, writes under `~/Documents/upstream/`, and raw `PA...`/`DU...`/`AK...`/`PK...` credential literals across AGY, Claude Code, and Codex.
2. **Path-Scoped SQLite WAL Peer-Lease Guard:** Query `~/.agents/bus/peer_bus.db` (`mode=ro`, `timeout=1.0`) on `write_file`/`edit_file` and return `decision="ask"` whenever another active session holds an overlapping path pattern (`fnmatchcase`) on the target repository, while allowing disjoint path leases cleanly.
3. **`PostToolUse` + `Stop` Self-Healing & `PreInvocation` Inbox Injection:** Run sub-50ms `ruff` `E9`/`F821` checks on edited Python files (`post_tool_lint.py` -> `stop_quality_gate.py` `decision="continue"`), inject unread peer-bus messages automatically on `SessionStart`/`PreInvocation`/`UserPromptSubmit`, and maintain strict `/usr/bin/python3` (`timezone.utc`) compatibility across all hook scripts.

## Alternatives Considered

1. **Repo-wide coarse mutex locking:** Rejected — needlessly blocks disjoint parallel work (e.g., `README.md` vs `src/agy_sota/prewall_study.py`).
2. **Assuming `mise` Python `3.14` in hook shebangs:** Rejected — hooks invoked under default system `/usr/bin/python3` failed on `from datetime import UTC` until standardized on `timezone.utc`.

## Verification Witness

- `harness/run_probes.py` `L1` & `L12` verify hard `deny` on live-bin, `api.alpaca.markets`, `:4001`, and `~/Documents/upstream/`, `ask` on overlapping `peer_leases`, `PostToolUse`->`Stop` `continue` self-healing, and `peer_hook_adapter.py` inbox/firewall parity.
- `~/.agents/bin/sota-doctor` `L5` verifies hook execution under `/usr/bin/python3` (`PASS`).
