# ADR-0001: AGY SOTA Harness Boundaries, Upstream-First Discipline & Runtime-Enforced Verification Bar

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** Cross-Cutting (`L0–L12` × `T0–T8` × `P0–P5`)
- **Evidence Grade:** E4 (Runtime-Probed Across 13 Layers & 10 `sota-doctor` Gates)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/native-agent-stack, https://github.com/native-agent-stack/dsh-sota-harness (`6656bb86752cbeb1b2be160a26bc5dac94c04f04`), https://github.com/google-antigravity/antigravity-sdk-python (`agy@1.5.3`), https://github.com/github/spec-kit (`2026-SOTA`)
- **Revisit Trigger:** 2027-01-01 (45-day cadence) or any Antigravity 2.0 hook/plugin/MCP protocol change

## Context and Problem Statement

Prose instructions in `AGENTS.md` and `GEMINI.md` degrade over long multi-step trajectories, while fragmented `.gemini/`, `.claude/`, and `.codex/` configurations leave skills dark across peer agents and bloated MCP server lists consume context budgets before turn 1. Antigravity (`AGY`) requires an offline, deterministic harness (`L0–L12`) unifying global charters (`<= 45` lines per ETH Zurich `arXiv:2602.11988`), fail-closed runtime hooks, symbol-level AST/FTS5 retrieval, MADR 4.0 ADR governance, and cross-peer convergence alongside `~/Documents/cc-sota-harness` and `~/Documents/dsh-sota-harness`.

## Decision Outcome

1. **Executable Guards Over Prose (`L1`, `L8`, `L9`):** Enforce live-capital refusal (`.claude/bin/live`, `api.alpaca.markets`, IBKR live ports `4001`/`7496`), `~/Documents/upstream/` read-only immutability, active `peer_bus.db` lease collision prompts, and `gitleaks` secret/account-ID blocking inside `PreToolUse`, paired with `PostToolUse` + `Stop` `ruff` syntax/undefined-name self-healing.
2. **Upstream-First & Zero Reinvention (`L0–L12`, `T0–T8`):** Every tracked module, workflow, AST rule, and policy in `upstream-map.toml` must map to a maintained GitHub upstream in `UPSTREAM.md` and pass `scripts/merge_gate.py` against all 18 SHA-pinned clones in `~/Documents/upstream/`.
3. **One-Owner-Per-Surface Multi-Peer Triad (`P0–P5`):** Converge Antigravity (`agy-sota-harness`), Claude Code (`cc-sota-harness`), OpenAI Codex (`~/.codex/`), DeepSeek Harness (`dsh-sota-harness`), and Orca (`stablyai/orca`) over one shared SQLite WAL peer bus (`~/.agents/bus/peer_bus.db`) and canonical skill root (`~/.agents/skills/`).
4. **MADR 4.0 Zero-Drift Catalog (`L4`):** Require every architectural boundary to carry a uniquely numbered `ADR-XXXX` record with GitHub primary-source URLs, verified fail-closed by `scripts/architecture_catalog.py --check` inside `scripts/merge_gate.py`.

## Alternatives Considered

1. **Prose-only `GEMINI.md` / `AGENTS.md` rules (>200 lines):** Rejected — increases context bloat and cannot block live-broker commands, secret leaks, or peer-lease collisions below the model.
2. **Separate per-agent skill copies and isolated memory stores:** Rejected — causes immediate configuration drift across Antigravity, Claude Code, Codex, and Orca worktrees.

## Verification Witness

- `mise exec -- uv run python scripts/merge_gate.py` -> `[AGY-MERGE-GATE PASS]`
- `mise exec -- uv run python scripts/architecture_catalog.py --check` -> `14 ADRs valid, 0 drift`
- `mise exec -- uv run python harness/run_probes.py` -> `13/13 probes PASSED` (`<3s`, zero network calls)
- `~/.agents/bin/sota-doctor` -> `10/10 PASS`
