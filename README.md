# AGY SOTA Practice & Verification Harness (`L0–L9`)

Runnable offline verification harness for the Antigravity (`AGY`) multi-repo workflow stack — the AGY counterpart to `~/Documents/dsh-sota-harness`.

## Quick Start

```sh
python3 harness/run_probes.py
```

Runs all 10 layer probes (`L0–L9`), warms/verifies the read-only SQLite FTS5 index over all 18 pinned upstream clones (`~/Documents/upstream/PINS.md`) + cross-repo ADRs, exercises `PreToolUse` / `PostToolUse` / `Stop` hooks against adversarial payloads, checks `sota-mover-ranker/scripts/merge_gate.py`, and writes `cache/session_brief.json` + `cache/SKILLOPT_DIGEST.md`.

## Probe Matrix (`L0–L9`)

| Layer | Target Surface | Contract Verified |
| :--- | :--- | :--- |
| **L0** | Packaging & Cross-Repo Bridges | `agy-sota-core` plugin manifest, `~/Documents/.agents-core/skills.json`, and all 9 bridged repos resolve cleanly |
| **L1** | Lifecycle Hooks (`hooks.json`) | `PreToolUse` hard-denies `.claude/bin/live`, `:4001`/`:7496`, `upstream/` writes & raw API keys; `PostToolUse` + `Stop` catch & clear Python `F821` errors |
| **L2** | Lean MCP JSON-RPC `2025-03-26` | `sota_core_mcp.py` boots over stdio, exposes 5 typed tools, and keeps global MCP server count within the Lean `<= 6` budget |
| **L3** | AST Graph & Pinned-Shelf FTS5 | `sota_symbol_lookup`, `sota_ast_search` (`sg`), and `sota_shelf_search` resolve exact symbols/ADRs/`upstream/` pins with zero dirty shelf files |
| **L4** | Progressive-Disclosure Skills | Valid YAML frontmatter (`name`, `description`), `<24 KB` rule cap, and 37 `.claude/skills` mounted across `claude-trading-skills` & `edge` |
| **L5** | Typed `run_workflow` DAGs | AST validity, `phase()` + typed `schema` contracts, and zero hardcoded local home-path leaks across shared workflows |
| **L6** | Design Taste & DevTools | `sota-taste-anti-slop` skill + `chrome-devtools-plugin` registration |
| **L7** | Context-Mode Output Sandbox | `sota_compressed_exec` indexes full output into SQLite FTS5 and achieves compressed salient slices |
| **L8** | Security, Binaries & Merge Gate | Verifies `ruff`, `ty`, `sg`, `gitleaks`, sidecar `access_grants`, public-tree privacy regexes, and `sota-mover-ranker` merge gate |
| **L9** | `SkillOpt` Trajectory Readiness | Runs redacted `sota_trajectory_friction` over AGY `transcript.jsonl` logs and emits `cache/SKILLOPT_DIGEST.md` |
