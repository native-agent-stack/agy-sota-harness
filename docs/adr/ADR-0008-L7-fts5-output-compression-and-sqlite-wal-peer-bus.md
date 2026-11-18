# ADR-0008: L7 SQLite FTS5 Output Compression, Shared WAL Peer Bus & Auto-Compiled LLM-Wiki

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `L7` Context Efficiency & Cross-Peer Persistent Memory
- **Evidence Grade:** E4 (`93.1%` Byte Compression & `4/4` Auto-Compiled Wiki Ledgers Verified)
- **GitHub Evidence:** https://github.com/mksglu/context-mode (`99c5f38b622c`), https://github.com/rtk-ai/rtk (`v1.2.0`), https://github.com/gastownhall/beads (`7ef2fd05e`), https://github.com/OthmanAdi/planning-with-files (`51bf62def62d`), https://github.com/volcengine/OpenViking (`0.5.5`)
- **Revisit Trigger:** 2027-01-01 or SQLite WAL contention / FTS5 schema evolution

## Context and Problem Statement

Verbose `pytest`, `ruff`, and diagnostic dumps flood LLM context windows, while ephemeral chat memory vanishes across compaction boundaries and remains invisible to concurrent peer sessions (`Antigravity`, `Claude Code`, `Codex`, `Orca`).

## Decision Outcome

1. **SQLite FTS5 Tool-Output Sandbox (`sota_compressed_exec`):** Execute read-only diagnostics, store full output in local SQLite FTS5, and return only high-signal error/summary slices (`>90%` byte reduction).
2. **Shared SQLite WAL Peer Bus (`~/.agents/bus/peer_bus.db`) & Auto-Compiled Wiki (`~/.agents/wiki/`):** Centralize atomic file leases (`peer_leases`), cross-session messages (`peer_messages`), repository handovers (`handovers`), graded root-cause lessons (`lessons`), and immutable SHA-256 hypothesis pre-registrations (`hypotheses`), automatically compiling `ACTIVE_PEERS.md`, `HANDOVER.md`, `LESSONS.md`, and `HYPOTHESIS_LEDGER.md` on every write.

## Alternatives Considered

1. **Unstructured markdown append-only files without SQLite WAL:** Rejected — suffers concurrent write races across simultaneous multi-agent sessions and lacks sub-10ms FTS5 BM25 retrieval.
2. **External cloud vector databases:** Rejected — adds network latency, credential surface, and privacy exposure for local repository memory.

## Verification Witness

- `harness/run_probes.py` `L7` verifies `>= 50%` (`93.1%` observed) byte savings on `sota_compressed_exec` and `sota-bus` / `sota-core` CLI availability.
- `~/.agents/bin/sota-doctor` `L7` verifies `WAL` journal mode and `4/4` compiled `~/.agents/wiki/*.md` files.
