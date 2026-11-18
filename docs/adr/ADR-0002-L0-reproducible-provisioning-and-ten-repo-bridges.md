# ADR-0002: L0 Reproducible Polyglot Provisioning, Lockfiles & 10-Repository Skill Bridges

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `L0` Provisioning & Cross-Repo Topology
- **Evidence Grade:** E4 (Lockfile & 10-Repo Bridge Probed)
- **GitHub Evidence:** https://github.com/jdx/mise (`2026.11.6`), https://github.com/astral-sh/uv (`0.13.7`), https://github.com/python/cpython (`3.14.10`), https://github.com/astral-sh/ruff (`0.17.5`), https://github.com/astral-sh/ty (`0.0.105`), https://github.com/ast-grep/ast-grep (`0.51.3`), https://github.com/stablyai/orca (`1.4.255`)
- **Revisit Trigger:** 2027-01-01 or `mise` / `uv` / CPython minor baseline bump

## Context and Problem Statement

macOS GUI applications (`Antigravity.app`, `Orca.app`) launch stdio MCP servers and lifecycle hooks with minimal `PATH` environments where bare `mise` shims fail outside directories containing a `mise.toml`. Simultaneously, 10 sibling quantitative and harness repositories under `~/Documents/*` and `~/canon` need deterministic access to shared engineering and trading skills without duplicating files.

## Decision Outcome

1. **Deterministic Tool & Package Locks (`mise.toml` + `mise.lock`, `pyproject.toml` + `uv.lock`):** Pin CPython `3.14.10`, `uv@0.13.7`, `ruff@0.17.5`, `ty@0.0.105`, `ast-grep@0.51.3`, `ripgrep@15.2.0`, `fd@10.5.2`, `duckdb@2.0.0`, `gitleaks@8.30.1`, and `hcom@0.7.31` with committed lockfiles.
2. **Direct Interpreter Paths for GUI MCP Spawns:** Configure GUI-spawned MCP entries (`~/.gemini/config/mcp_config.json` and plugin `mcp.json` manifests) to invoke concrete `mise/installs/...` or `.venv/bin/python` binaries with `PYTHONUNBUFFERED=1` and `--no-project` where needed, eliminating macOS GUI shim failures.
3. **10-Repository `.agents/skills.json` Bridges + `orca.yaml`:** Maintain `.agents/skills.json` inheritance bridges across `claude-trading-skills`, `edge`, `meridian`, `movers`, `sota-mover-ranker`, `trading-sota`, `tsl`, `dsh`, `dsh-sota-harness`, and `~/canon`, paired with workspace `orca.yaml`.

## Alternatives Considered

1. **Homebrew-only unpinned global binaries:** Rejected — non-reproducible across upgrades and lacks per-repo lockfile provenance.
2. **Relying on `~/.local/share/mise/shims/uv` in GUI `mcp_config.json`:** Rejected — empirically failed (`exit 1: No version is set for shim: uv`) when Antigravity spawned MCPs with `cwd=/`.

## Verification Witness

- `harness/run_probes.py` `L0` verifies `mise.toml`, `pyproject.toml`, `orca.yaml`, `UPSTREAM.md`, `upstream-map.toml`, `SOTA_ECOSYSTEM_MANIFEST.json`, and all `10` bridged `.agents/skills.json` manifests (`PASS`).
