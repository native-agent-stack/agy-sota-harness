# AGY Full-Landscape SOTA Harness Framework (`L0–L12` × `T0–T8` × `P0–P5` Peers)

The machine-wide Antigravity (`AGY`) SOTA Harness & Multi-Peer Convergence repository — completing the ecosystem triad alongside `~/Documents/cc-sota-harness` (Claude Code) and `~/Documents/dsh-sota-harness` (DeepSeek Harness) over a single shared SQLite WAL peer bus (`~/.agents/bus/peer_bus.db`) and 18-repo pinned upstream shelf (`~/Documents/upstream/PINS.md`).

## Quick Verification (`Done` Bar)

```sh
mise exec -- uv run python scripts/sync_vendored_skills.py
mise exec -- uv run python scripts/merge_gate.py
mise exec -- uv run python harness/run_probes.py
mise exec -- uv run pytest
mise exec -- ruff check .
```

## Full-Landscape Architecture (`L0–L12` × `P0–P5`)

| Layer | Surface | Enforced SOTA Capability |
| :--- | :--- | :--- |
| **L0** | Provisioning | `mise.toml` (`mise.lock`, 22 CLI pins incl. `agy 1.5.3`) + `pyproject.toml` (`uv.lock`) + `orca.yaml` |
| **L1** | Lifecycle Hooks | `PreToolUse` (live-broker/port/host deny + `gitleaks` + **live `peer_bus.db` lease collision guard**), `PostToolUse` + `Stop` (`ruff` `E9`/`F821` self-healing) |
| **L2** | Lean MCP Mesh | 4 active servers (`<= 6` Lean budget): `agy-sota-core` (7 tools), `sota-peer-bus` (7 tools), `sota-mover-ranker-stdio` (13 tools), `alpaca-sota-watchlists` |
| **L3** | Code Graph & Shelf | `sota_symbol_lookup`, `sota_ast_search`, `sota_ast_lint_audit`, `sota_shelf_search` (`3,110+` docs SQLite FTS5 BM25), `codebase-memory-mcp`, `codegraph` |
| **L4** | Converged Skills | **16** canonical `~/.agents/skills/*` mounted across **AGY + Claude + Codex** + **8** pinned scientific/security skills + **10** bridged repos (`~/Documents/*` + `~/canon`) |
| **L5** | Typed Workflows | 4 schema-typed `run_workflow` Python DAGs (`src/agy_sota/workflows/`) + **9** self-bootstrapping `~/.agents/workflows/REGISTRY.json` pipelines (`/sota-workflow`) + AGY Native Swarm (`workspace:"share"` + 1:3 verifiers) |
| **L6** | UI Taste & DevTools | `sota-taste-anti-slop` (`impeccable` + `taste-skill` + `hallmark`) + `chrome-devtools-plugin` + `perspective` / `lightweight-charts` |
| **L7** | Context & Memory | `sota_compressed_exec` (`>90%` byte reduction via SQLite FTS5), `beads` (`bd`), `OpenViking`, `~/.agents/wiki/{ACTIVE_PEERS,HANDOVER,LESSONS,HYPOTHESIS_LEDGER}.md` |
| **L8** | Formal Invariants | `src/agy_sota/{invariants,prewall_study,intraday_prewall_study}.py` (`ADR-0022 <= 2.00%` NMS tick-grid stops, dimensional `bps`/`pct`/`ratio`, `<= 2026-10-15` pre-wall, HLZ `t*(N)`, `Pandera` OHLCV, DuckDB 1m SIP + `CPCV`/`DSR`) + `Hypothesis` fuzzing + 4 `ast-grep` YAML rules |
| **L9** | OS Sandbox & Privacy | `@anthropic-ai/sandbox-runtime` (`policies/srt-agy-worker.json`), `.gitleaks.toml`, `.githooks/pre-commit`, `scripts/merge_gate.py` |
| **L10** | Observability | Scheduled AGY Sidecar (`*/20` market hours), `agentsview`, `cache/session_brief.json` |
| **L11** | Trading & GUI | 18/18 read-only `~/Documents/upstream/` pinned clones + `agent-desktop` (`TradingView.app`) + `agent-browser` |
| **L12** | Self-Evolution | `sota_trajectory_friction` + `sota_ecosystem_convergence` + 6 custom AGY subagents (`sota-rd-proposer`, `sota-falsifier`, `sota-code-verifier`, `sota-deep-synthesizer`, `sota-skillopt-curator`, `sota-subsession-orchestrator`) |
