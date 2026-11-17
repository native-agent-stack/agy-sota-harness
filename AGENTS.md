# AGENTS.md — AGY Full-Landscape SOTA & Multi-Peer Convergence Harness (`agy-sota-harness`)

## Non-Negotiable Operating Charter
1. **Upstream-First Provenance:** Every tracked file maps in `upstream-map.toml` to a verified row in `UPSTREAM.md` and `~/Documents/upstream/PINS.md`, enforced fail-closed by `scripts/merge_gate.py`. Anything unverified against primary source this session is labeled `UNVERIFIED`.
2. **Runtime-Enforced Boundaries (Hooks + AST + Seatbelt):**
   - **Hard Live-Capital Firewall:** `api.alpaca.markets`, `.claude/bin/{live,alpaca-live-mcp,key-store}`, and live IBKR ports (`4001`, `7496`) are hard-refused across `PreToolUse`, `rules/ast-grep/`, and `policies/srt-agy-worker.json`.
   - **Paper & Stop Standard (`ADR-0022`):** Paper lanes (`PA...` `<= 200 req/min`, `DU...` `:4002` `<= 3,000 msg/min`) enforce atomic `<= 2.00%` protective stops (`agy_sota.invariants.validate_adr0022_stop`).
   - **Pre-Wall Statistical Gate (`<= 2026-10-15`):** Factor selection, `CombinatorialPurgedCV`, Deflated Sharpe (`DSR`), and Harvey–Liu–Zhu `t*(N)` pre-registration (`sota_bus_hypothesis_ledger`) strictly observe `<= 2026-10-15`.
   - **Cross-Peer Lease Safety:** Check `sota_bus_status` / `sota_bus_claim_work` (`~/.agents/bus/peer_bus.db`) before editing shared repos; `PreToolUse` prompts on overlapping active peer leases.
   - **Zero Secret / Path Leaks:** Never print, log, or commit keys, tokens, `PA...`/`DU...` IDs, raw dollar balances, or hardcoded local home paths.
3. **Empirical `Done` Definition:**
   Run and report verbatim pass counts for:
   `mise exec -- uv run python scripts/merge_gate.py && mise exec -- uv run python harness/run_probes.py && mise exec -- uv run pytest && mise exec -- ruff check .`
