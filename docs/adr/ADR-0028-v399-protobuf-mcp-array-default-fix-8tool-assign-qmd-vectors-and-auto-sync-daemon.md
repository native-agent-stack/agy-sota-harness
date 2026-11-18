# ADR-0028: `v3.9.9` Antigravity Protobuf MCP Array-Default Fix (`8/8` Tools Live), `2,325`-Vector `qmd` Embed, `sota-auto-sync` Daemon & `8`-Runtime Co-op Parity

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Antigravity `L0–L13` Harness, Native MCP Schema (`L2`/`L3`), Semantic Memory (`L7`) & Background Automation (`L10`)
- **Evidence Grade:** E4 (`28` ADRs, Live `call_mcp_tool("sota_bus_assign_worker")` & `sota_bus_claim_work`, `2,325` `qmd` Vectors, `com.sota.3surface-memory-qmd-sync` LaunchAgent & `13/13` Probes Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/tobi/qmd, https://github.com/stablyai/orca
- **Revisit Trigger:** 2027-01-02 or Ecosystem `v4.0.0` promotion

## Context and Problem Statement

Post-restart inspection of Antigravity's auto-generated MCP tool schemas (`~/.gemini/antigravity/mcp/sota-peer-memory-and-council_sota-peer-bus/*.json`) and `cc-lead` `Msg #173` revealed three concrete runtime issues:
1. **Protobuf `Struct` Array-Default Rejection:** Setting `"default": ["*"]` on `"paths": {"type": "array"}` inside `peer_bus_mcp.py` caused Antigravity's MCP schema converter to emit `"parameters": null` on both `sota_bus_claim_work` and `sota_bus_assign_worker`.
2. **`qmd` Recursive `update-cmd` & Missing Dense Vectors:** Pointing `qmd collection update-cmd` at a wrapper that itself called `qmd update` caused 30s timeout recursion, and `580` indexed docs had `0` embedded vectors.
3. **Sidecar & Zero-Token Background Sync:** AGY's scheduled sidecar (`sota-early-mover-paper-goal/sidecar.json`) needed explicit `mcp(.../sota_bus_assign_worker)` + `command(.../sota-workstation)` grants, and inter-session 3-surface sync required a zero-token `LaunchAgent`.

## Decision Outcome

1. **Remove Array `"default"` from `peer_bus_mcp.py` (`8/8` Native MCP Tools Live):**
   - Keep default `["*"]` fallback inside `_dispatch_tool()` while omitting `"default"` on `type: "array"` properties; verified post-fix via live `call_mcp_tool("sota_bus_assign_worker")` (`memory_hits_injected: 6`) and `call_mcp_tool("sota_bus_claim_work")`.
2. **Embed `2,325` `qmd` Vectors & Non-Recursive `--mirror-only` `update-cmd`:**
   - Run `qmd embed` (`embeddinggemma-300M-Q8_0.gguf`, `2,325` chunks across `580` docs, `21.6 MB` index) and bind `qmd collection update-cmd sota-adrs` to `sota-auto-sync --mirror-only`.
3. **Enable `com.sota.3surface-memory-qmd-sync` (`900s`, `ProcessType=Background`, `Nice=10`) & Sidecar Grants:**
   - Run zero-token OMC callback ingestion, `qmd update`, and lease-safe 3-surface Git + memory delta sync every 15 minutes without touching `:8787` / `:8799` / `:4002` RTH sockets.

## Alternatives Considered

- **Invoking `sota-bus` exclusively via shell CLI instead of fixing the MCP `inputSchema`:** Rejected — native `call_mcp_tool` enforces JSON-schema argument validation across AGY and subagents.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` -> `28 GitHub-evidenced ADRs valid, 0 drift`
- `python3 harness/run_probes.py` -> `13/13 probes PASSED`
- `uv run pytest -q && python3 scripts/merge_gate.py && gitleaks git --staged --no-banner` -> `21/21 PASS`, `[AGY-MERGE-GATE PASS]`, `0` leaks
