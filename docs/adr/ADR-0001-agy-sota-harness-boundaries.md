# ADR-0001: AGY SOTA Harness Boundaries & L0–L9 Verification Bar

- **Status:** Accepted
- **Date:** 2026-11-17

## Context
Prose instructions in `AGENTS.md` degrade over long multi-step trajectories, while fragmented `.claude/` vs `.agents/` layouts leave skills dark across repositories and bloated MCP configurations waste context tokens. Modeled on `~/Documents/dsh-sota-harness`, Antigravity requires an offline, executable verification harness (`L0–L9`) enforcing deterministic hooks, lean AST/FTS5 retrieval, and cross-repo skill inheritance.

## Decision
1. **Executable Guards Over Prose (`L1`, `L8`):** Enforce live-capital refusal (`.claude/bin/live`, IBKR ports `4001`/`7496`), `~/Documents/upstream/` immutability, and `gitleaks` secret gating inside `PreToolUse`, plus incremental `ruff` syntax/undefined-name checks across `PostToolUse` + `Stop`.
2. **Shared Cross-Repo Inheritance (`L0`, `L4`):** Centralize portable engineering skills and schema-typed `run_workflow` scripts in `~/Documents/.agents-core/`, inherited via `.agents/skills.json` across all repositories while bridging `.claude/skills` in `.claude`-native repos.
3. **Lean Local AST + FTS5 Shelf MCP (`L2`, `L3`, `L7`):** Provide symbol-level AST lookup, `ast-grep` structural search, read-only SQLite FTS5 BM25 indexing over all 18 `~/Documents/upstream/` clones + ADRs, and FTS5 compressed command execution inside a single stdio MCP server (`agy-sota-core`), keeping total global MCP servers `<= 6`.
4. **Trajectory Self-Evolution (`L9`):** Mine redacted `transcript.jsonl` logs via `sota_trajectory_friction` to drive validation-gated `SKILL.md` and `hooks.json` refinements (`SkillOpt` / `/learn`).

## Consequences
- Every customization change can be verified in `<5s` via `python3 harness/run_probes.py` with zero network calls and zero dirty mutations to `~/Documents/upstream/` or clean working repositories.
