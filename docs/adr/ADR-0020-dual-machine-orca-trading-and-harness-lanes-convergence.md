# ADR-0020: `v3.7.0` Dual-Machine (`Mac M5 Max <-> Noesis`) Orca Trading Lanes (`T1–T3`), Harness Lanes (`H1–H3`) & 11-Repo `orca.yaml` Fleet Convergence

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Dual-Machine Orca Fleet, Trading Execution Lanes & Multi-Runtime Harness Topology (`L0–L12` × `P0–P5` × `T0–T8`)
- **Evidence Grade:** E4 (`11/11` Cross-OS `orca.yaml` Recipes, `6/6` Local AGY DAGs, `13/13` AGY Probes PASS, `4/4` Public GitHub Actions CI `completed/success`)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-compounding-lab, https://github.com/native-agent-stack/sota-mover-ranker, https://github.com/native-agent-stack/sota-dynamic-trail-c, https://github.com/native-agent-stack/dsh-sota-harness, https://github.com/native-agent-stack/sota-upstream-shelf-lock, https://github.com/native-agent-stack/dsh-plugin-landscape, https://github.com/stablyai/orca
- **Revisit Trigger:** 2027-01-02 (45-day cadence) or `2026-12-06` Consolidated `SIP` `23/5` cutover

## Context and Problem Statement

While `ADR-0018` (`v3.5.0`) and `ADR-0019` (`v3.6.0`) converged the `14` multi-model workflows, `7`-feed `sota-research-feeds.v2` PIT contract, and `3`-surface repo layout (`Apple M5 Max` `macOS` `~/Documents/*`, stationary `Noesis` `Windows` `C:/sota-workstation/*`, and `WSL2 Noesis-Carbon` `~/sota-workstation/*`), only `5` repositories carried a deterministic `orca.yaml` worktree setup recipe (`agy-sota-harness`, `astrolabe`, `cc-sota-harness`, `meridian`, `sota-harness-foundation`). Spawning isolated Orca child worktrees (`:6770`) on the remaining trading and harness repositories (`sota-compounding-lab`, `sota-mover-ranker`, `sota-dynamic-trail-c`, `dsh-sota-harness`, `sota-upstream-shelf-lock`, `dsh-plugin-landscape`) lacked `setupAgentStartupPolicy: wait-for-setup` environment hydration and explicit `T1..T3` / `H1..H3` dual-machine lane audit coverage in `agy-sota-harness`.

## Decision Outcome

1. **Standardize Cross-OS `orca.yaml` Workspace Recipes Across `11` Active Repositories (`T1–T3` & `H1–H3`):**
   - Land zero-leak, cross-OS (`macOS` + `Windows` + `WSL2 Noesis-Carbon`) `orca.yaml` recipes (`setupAgentStartupPolicy: wait-for-setup`, zero `/Users/` paths, zero daemon restarts on live `:8787` / `:8799`) across `sota-compounding-lab`, `sota-mover-ranker`, `sota-dynamic-trail-c`, `dsh-sota-harness`, `sota-upstream-shelf-lock`, and `dsh-plugin-landscape`, bringing verified `orca.yaml` fleet coverage in `~/Documents/*` to `11` repositories enforced by `probe_l0()`.
2. **Add Repo-Local Workflow `#6` (`dual_machine_trading_and_harness_lanes_workflow.py`):**
   - Introduce a schema-typed `run_workflow` DAG bound to `kit.load_research_convergence_context()` and `kit.verify_workflow_research_convergence()` auditing Trading Lanes `T1` (Sim / Pre-Wall `<= 2026-10-15` / 18-Clone Shelf Lock), `T2` (`:8787` Alpaca Paper `<= 200/min` + `:4002` IBKR Paper `<= 3,000/min` with single-active-broker-host split-brain firewall), and `T3` (`:8799` `24/5` Near-Lossless Guardian + Empirical-Bayes Compounding + Private Vault) alongside Harness Lanes `H1` (`cc-lead` `OMC` v2 + Foundation), `H2` (`AGY` `L0–L12` + `14` `MMW` DAGs), and `H3` (`DSH` + `Codex OMX` + `OpenCode OMO` + `Composio AO` + `Orca` `:6770` + `hcom` / `sota-peer-bus`).
3. **Upgrade `SOTA_ECOSYSTEM_MANIFEST.json` to `manifestVersion = "3.7.0"` (`20` MADR 4.0 ADRs):**
   - Record `dualMachineOrcaLanes` (`tradingLanes` `T1..T3` & `harnessLanes` `H1..H3`) and `multiModelOrchestrationFrameworks` (`8` converged orchestration runtimes) with deterministic regression gates in `harness/run_probes.py` (`L0`, `L4`, `L5`) and `tests/test_agy_sota_ecosystem.py`.

## Alternatives Considered

1. **Rely on manual shell setup inside newly spawned Orca worktrees on `Mac M5 Max` or `Noesis`:** Rejected — violates `setupAgentStartupPolicy: wait-for-setup` determinism and risks running agents before `uv sync --locked` or Node probe verification completes.
2. **Include `:8787` or `:8799` daemon start commands in `orca.yaml` `defaultTabs`:** Rejected — child worktrees must never spawn competing `:8787`/`:8799` listeners or interrupt active RTH paper daemons (`single-active-broker-host` split-brain firewall).

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` -> `20 GitHub-evidenced ADRs valid, 0 drift`
- `python3 scripts/merge_gate.py` -> `[AGY-MERGE-GATE PASS]`
- `python3 harness/run_probes.py` -> `13/13 probes PASSED` (`>= 11` `orca.yaml` repos in `L0`, `20` ADRs in `L4`, `6` DAGs in `L5`)
- `uv run pytest -q`, `ruff check .`, `ty check src scripts harness`, & `gitleaks detect --no-git .` -> `100% PASS` (`0` leaks)
