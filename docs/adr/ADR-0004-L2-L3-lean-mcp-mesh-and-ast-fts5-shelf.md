# ADR-0004: L2–L3 Lean 4-Server MCP Mesh, AST Symbol Graph & 18-Repo Read-Only Shelf FTS5

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `L2` Lean MCP Mesh & `L3` Code Intelligence / Shelf Retrieval
- **Evidence Grade:** E4 (Live `2025-03-26` JSON-RPC Handshakes & `<10ms` FTS5 Verified)
- **GitHub Evidence:** https://github.com/DeusData/codebase-memory-mcp (`v0.12.1`), https://github.com/colbymchenry/codegraph (`1.6.3`), https://github.com/ast-grep/ast-grep (`0.51.3`), https://github.com/alpacahq/alpaca-mcp-server (`63cc4278d87b31f3ed4efcfaa55624095c6d7be8`), https://github.com/native-agent-stack/sota-mover-ranker (`bb1d90b10a95333975ced7e4d16c59d5e67f5e94`)
- **Revisit Trigger:** 2027-01-01, MCP protocol revision beyond `2025-03-26`, or active MCP server count approaching `6`

## Context and Problem Statement

Loading dozens of overlapping third-party MCP servers inflates tool-schema overhead and degrades tool-selection accuracy, while reading entire `1,000+`-line Python files or guessing upstream API signatures (`alpaca-py`, `nautilus_trader`, `skfolio`, `ml4t-diagnostic`, `polars`, `duckdb`, `hftbacktest`) wastes 90%+ of context tokens and risks hallucinated parameters.

## Decision Outcome

1. **Strict `<= 6` Active MCP Server Budget (`4` Active Servers):**
   - `agy-sota-core` (`7` tools: `sota_symbol_lookup`, `sota_ast_search`, `sota_ast_lint_audit`, `sota_shelf_search`, `sota_compressed_exec`, `sota_trajectory_friction`, `sota_ecosystem_convergence`)
   - `sota-peer-bus` (`7` tools: `sota_bus_status`, `sota_bus_claim_work`, `sota_bus_handover_sync`, `sota_bus_record_lesson`, `sota_bus_hypothesis_ledger`, `sota_bus_search_memory`, `sota_bus_peer_message`)
   - `sota-mover-ranker-stdio` (`13` tools: live early-stage movers, zero-sell accumulation, watchlists, paper manifest, and goal-loop telemetry)
   - `alpaca-sota-watchlists` (pinned `alpacahq/alpaca-mcp-server@v2.4.1` strictly restricted to `ALPACA_PAPER_TRADE=true` and `watchlists,stock-data,corporate-actions,news`)
2. **AST Symbol Retrieval & Read-Only Shelf FTS5 BM25:** Index `3,110+` markdown/docstring/ADR chunks across all 18 `~/Documents/upstream/` clones into an external SQLite FTS5 index (`<10ms` BM25 queries, zero writes inside `~/Documents/upstream/`) and expose exact `file://#Lstart-Lend` AST spans via `sota_symbol_lookup`.
3. **Cross-Peer CLI Parity (`sota-core` & `sota-bus`):** Expose identical capabilities via `~/.agents/bin/sota-core` and `~/.agents/bin/sota-bus` so custom subagents (whose `agents/*.md` `tools:` lists accept only builtin host components, never `call_mcp_tool`) and Orca CLI workers have 100% parity.

## Alternatives Considered

1. **Adding `call_mcp_tool` to custom `agents/*.md` `tools:` YAML:** Rejected — empirically triggers `unknown component: tool "call_mcp_tool" not found in registry` (`Lesson a521070ef35a0922`); enforced via `sota-doctor` `L1`.
2. **Writing SQLite/tag indexes inside `~/Documents/upstream/`:** Rejected — pollutes clean upstream git worktrees and fails `merge_gate.py`.

## Verification Witness

- `harness/run_probes.py` `L2` & `L3` verify `2025-03-26` JSON-RPC `initialize` + `tools/list`, `total_active == 4 <= 6`, `sota_symbol_lookup`, and `sota_shelf_search` (`3,110` indexed docs in `<10ms`).
- `~/.agents/bin/sota-doctor` `L3` verifies live stdio handshakes (`7 + 7 + 13 = 27` local SOTA tools).
