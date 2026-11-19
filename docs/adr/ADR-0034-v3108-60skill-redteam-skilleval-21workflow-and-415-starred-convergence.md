# ADR-0034: `v3.10.8` 60-Skill, Red-Team, SkillEvaluator, 21-Workflow & 415-Starred Convergence

- **Status:** Accepted
- **Date:** 2026-11-19
- **Layer:** Antigravity `L0–L13` Harness, Canonical Skill Corpus (`60`), Red-Team Security & 4-Tier SkillEvaluator (`ADR-0043`), Dual-Machine Orca Fleet (`15` Automations) & `415+8` Starred Convergence (`H1–H3`)
- **Evidence Grade:** E4 (`34` GitHub-Evidenced ADRs, `10/10` Schema-Typed AGY `run_workflow` DAGs, `13/13` Live Harness Probes, `60/60` SkillEvaluator Pass, `pytest` & `merge_gate.py` `0` Leaks Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/elementalsouls/Claude-BugHunter, https://github.com/NVIDIA/SkillEvaluator, https://github.com/Tencent/LoopForge
- **Revisit Trigger:** Any addition of canonical skills beyond `60`, Orca workflow count changes beyond `21`, or modification of `UPSTREAM_SKILL_PINS.json` SHA-pinned upstream skills.

## Context and Problem Statement

With `v3.10.8`, the ecosystem expanded from `57` to `60` canonical skills (adding `sota-redteam-bughunter`, `sota-skill-evaluator`, and `sota-loopforge-convergence`), hardened `parabolic-short-trade-planner` to fail closed on `paper=True`, published the `sota-harness-foundation` `ADR-0043` Red-Team/4-Tier SkillEvaluator contract, added Workflow `#21` (`redteam-skilleval-convergence-loop`), and converged `415` owner-starred repositories plus `8` beyond-starred frameworks under `PHILOSOPHY_ONLY` authority. Meanwhile `agy-sota-harness/SOTA_ECOSYSTEM_MANIFEST.json` still reported `manifestVersion: "3.10.0"`, `orcaYamlFleetRepositories: 11`, `agy@1.5.3`, and `33` ADRs, while intentionally keeping `.agents/skills/` scoped cleanly to `UPSTREAM_SKILL_PINS.json`.

## Decision Outcome

1. **Advance `SOTA_ECOSYSTEM_MANIFEST.json` to `3.10.8`:** Record `orcaYamlFleetRepositories: 18`, `agy@1.5.10` (`gemini-4-neon-xhigh` flagship), `stablyai/orca@1.4.263`, `deepseek-v4.1-flash`, `10 Local DAGs + Native Swarm`, `21` `REGISTRY.json` workflows, and `v3108ConvergenceSummary` (`canonicalSkills: 60`, `canonicalWorkflows: 21`, `orcaAutomations: 15`, `ownerStarredAudited: 415`, `beyondStarredAnchors: 8`, `redteamSkillEvalAdr: "sota-harness-foundation/ADR-0043"`).
2. **Preserve Clean `UPSTREAM_SKILL_PINS.json` Scoping:** Keep `.agents/skills/` strictly scoped to SHA-pinned third-party upstream skills (`UPSTREAM_SKILL_PINS.json`) rather than duplicating the 60 global runtime skills inside the repo.
3. **Update Manifest & Governance Parity Tests:** Enforce `manifestVersion == "3.10.8"`, `adrCount == 34`, `canonicalSkills == 60`, and `canonicalWorkflows == 21` inside `tests/test_agy_sota_ecosystem.py` and verify zero drift via `scripts/architecture_catalog.py --sync-manifest` and `scripts/merge_gate.py`.

## Alternatives Considered

- **Duplicate all 60 canonical skill folders into `agy-sota-harness/.agents/skills/`:** Rejected because `agy-sota-harness` intentionally pins only external third-party skills with git SHAs in `UPSTREAM_SKILL_PINS.json`, while the canonical `60`-skill corpus lives in `~/.agents/skills/` and is synchronized via `sync-all-8-runtimes.py`.
- **Leave `SOTA_ECOSYSTEM_MANIFEST.json` at `3.10.0`:** Rejected because downstream `sota-org-doctor` and `test_agy_sota_ecosystem.py` require synchronized manifest, ADR catalog (`34` ADRs), and `v3.10.8` metadata.

## Verification Witness

- `uv run python scripts/architecture_catalog.py --sync-manifest` & `--check` (`34` GitHub-evidenced ADRs valid, `0` drift).
- `uv run python scripts/merge_gate.py` (`AGY-MERGE-GATE PASS`).
- `uv run ruff format --check .`, `uv run ruff check .`, `uv run pytest -q`, and `gitleaks git --staged --verbose` (`0` leaks).
