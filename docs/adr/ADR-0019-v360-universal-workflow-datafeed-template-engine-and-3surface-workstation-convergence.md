# ADR-0019: `v3.6.0` Universal `5/5` + `14/14` Workflow Research-Convergence, 6 DataFeed APIs, 4 Strategy Templates, 8 Engine Sources & 3-Surface Workstation Parity

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Full-Stack Workflow, DataFeed, Strategy Template, Engine Source & Dual-Workstation Governance (`L0–L12` × `P0–P5` × `T0–T8`)
- **Evidence Grade:** E4 (`5/5` Local AGY Workflows + `14/14` Canonical Registry Workflows Verified with `verify_workflow_research_convergence`, `13/13` AGY Probes PASS, `22/22` `pytest` PASS)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-compounding-lab, https://github.com/native-agent-stack/astrolabe, https://github.com/nautechsystems/nautilus_trader, https://github.com/nkaz001/hftbacktest
- **Revisit Trigger:** 2027-01-02

## Context and Problem Statement

Following `ADR-0018` (`v3.5.0` `cc-lead` 14-workflow hub convergence), the `5` native `src/agy_sota/workflows/*.py` pipelines needed explicit Turn-0 `verify_workflow_research_convergence(...)` envelope checks (`sota-workflow-research-convergence.v3.6`) and cross-surface repo path resolution (`resolve_repo_dir`) aligned with `sota-multi-model-workflows` `v3.6.0` (`ADR-0013` `@ 9f7c9aa6d3`) across **Apple M5 Max (`~/Documents/*`)**, **stationary `Noesis` Windows (`C:/sota-workstation/*`)**, and **clean `Noesis-Carbon` WSL2 (`~/sota-workstation/*`)**.

## Decision Outcome

1. **Bind All `5/5` Native AGY Workflows to `verify_workflow_research_convergence` (`v3.6.0`):**
   - Upgrade `cross_peer_orca_review_workflow.py`, `ecosystem_convergence_workflow.py`, `rd_agent_hypothesis_bus_workflow.py`, `research_convergence_landing_workflow.py`, and `skillopt_gepa_evolution_workflow.py` to execute `kit.verify_workflow_research_convergence(...)` at Turn-0 (`64`-hex `envelope_input_sha256`, `6` Trading Lane DataFeed APIs across `:8787`/`:8799`/`:4002`, `4` canonical strategy templates + Pine v6, `8` trading engine source repositories, `18` `40`-hex upstream pins, `<= 2026-10-15` pre-wall, `<= 2.00%` stop, and `PHILOSOPHY_ONLY` sibling-repo authority).
2. **Upgrade `SOTA_ECOSYSTEM_MANIFEST.json` to `manifestVersion = "3.6.0"` (`19` MADR 4.0 ADRs):**
   - Lock parity with `sota-multi-model-workflows` `v3.6.0` (`9f7c9aa6d3`) and add regression test coverage in `tests/test_agy_sota_ecosystem.py` enforcing `verify_workflow_research_convergence` across all `5/5` local workflow scripts.

## Alternatives Considered

1. **Leave `src/agy_sota/workflows/*.py` checking only `schema_version` strings without `verify_workflow_research_convergence`:** Rejected — allows drift between `L4` (`agy-sota-harness`) and `L7` (`sota-multi-model-workflows`) Turn-0 DataFeed/template/engine gates.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest` -> `19 GitHub-evidenced ADRs valid, 0 drift`
- `python3 scripts/merge_gate.py` -> `[AGY-MERGE-GATE PASS]`
- `python3 harness/run_probes.py` -> `13/13 probes PASSED`
- `uv run pytest -q`, `ruff`, `ty`, & `gitleaks` -> `100% PASS` (`0` leaks)
