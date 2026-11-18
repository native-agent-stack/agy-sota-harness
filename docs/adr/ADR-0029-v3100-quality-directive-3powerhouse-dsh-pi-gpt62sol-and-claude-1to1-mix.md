# ADR-0029: `v3.10.0` Quality-Directive `3`-Powerhouse + `DSH` + `Pi`/`OMP` (`gpt-6.2-sol` `high`) Parity & Claude Code `~1:1` Model-Mix Integration

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Cross-Harness Multi-Model Suitability Routing, MCP `sota_bus_assign_worker` & 3-Surface Parity (`L1` x `L3` x `L4` x `L8` x `L12`)
- **Evidence Grade:** E4 (`29` GitHub-Evidenced ADRs, `13/13` Live Harness Probes, `21/21` Pytest & Hypothesis Property Tests, Artificial Analysis `v5.0.1` / `v2.1` Grounded)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/cc-sota-harness, https://github.com/can1357/oh-my-pi
- **Revisit Trigger:** 2027-01-02 or Ecosystem `v4.0.0` promotion

## Context and Problem Statement

Antigravity (`gemini-4-carbon-high`, `#3` Artificial Analysis Intelligence Index & `#1` `1M+` long-horizon context) dispatches cross-family tasks via `sota_bus_assign_worker` MCP (`--worker auto`) and `run_workflow`. Under `v3.10.0`, the ecosystem converges active suitability routing onto our **3 Frontier Powerhouse Families + `DSH` + `Pi`/`OMP` (`gpt-6.2-sol` `high`)** while enforcing a **`~1:1` (`50%` `claude-fable-5-2` vs `50%` `claude-opus-5-5` + `claude-sonnet-5-5`)** model mix on Claude Code CLI (`0%` `haiku` sprawl).

## Decision Outcome

1. **Expand `sota_bus_assign_worker` MCP & `sota_bus_engine.py` Worker Presets for `v3.10.0`:**
   - Support `auto`, `claude` (`claude-fable-5-2` `xhigh`), `claude-opus` (`claude-opus-5-5` `high`), `claude-sonnet` (`claude-sonnet-5-5` `high`), `codex` (`gpt-6.2-astra` `xhigh`), `codex-sol` (`gpt-6.2-sol` `high`), `omp` / `pi` (`@worker -> openai-codex/gpt-6.2-sol` `high`), `dsh` (`deepseek-v4-pro` `high`), and `antigravity` (`gemini-4-carbon-high` `high`).
2. **Harden Cross-Workstation Ephemeral Python Execution (`sota_ephem.py`):**
   - Execute chunked remote payloads via `$env:TEMP\sota_ephem.py` rather than `python.exe -c $c` so payloads `> 32 KB` (`sota_bus_engine.py` + `peer_hook_adapter.py` 3-surface mirrors) bypass Win32 `CreateProcessW` command-line limits cleanly.
3. **Advance `SOTA_ECOSYSTEM_MANIFEST.json` to `manifestVersion = "3.10.0"` (`29` ADRs):**
   - Maintain 100% parity with `sota-multi-model-workflows` (`ADR-0023`), `cc-sota-harness` (`ADR-0035`), `sota-harness-foundation` (`ADR-0036`), and `canon` (`0185`).

## Alternatives Considered

- **Routing AST refactors through unauthenticated secondary runtimes:** Rejected — `claude-sonnet-5-5` (non-GPT `Hephaestus`) + `gpt-6.2-sol` (`codex-sol` / `omp` / `pi`) deliver authenticated frontier quality on both Mac and Noesis.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` (`29` GitHub-evidenced ADRs valid, `0` drift)
- `python3 harness/run_probes.py` (`13/13 probes PASSED`)
- `uv run pytest -q` (`21 passed`) & `python3 scripts/merge_gate.py` (`AGY-MERGE-GATE PASS`)
