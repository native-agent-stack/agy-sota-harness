# ADR-0024: v3.9.3 Starred Visual, Editorial Diagramming, Knowledge-Graph & Illustration Craft Atlas, Probation EB Throttle & Dual-TV Coexistence

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Antigravity `L0–L13` Harness, Institutional Visual/Diagram Craft (`L6`/`L8`/`L9`) & 3-Surface Convergence (`H0–H7` × `T1–T5`)
- **Evidence Grade:** E4 (`24` Curated Starred Craft Repos from `404` Stars, `17` Canonical Multi-Peer Skills, `24` ADRs & `21/21` Pytest Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/agy-sota-harness, https://github.com/tt-a1i/archify, https://github.com/cathrynlavery/diagram-design, https://github.com/likec4/likec4, https://github.com/Graphify-Labs/graphify, https://github.com/Egonex-AI/Understand-Anything, https://github.com/Leonxlnx/taste-skill, https://github.com/pbakaus/impeccable, https://github.com/ZSeven-W/openpencil, https://github.com/backnotprop/plannotator
- **Revisit Trigger:** 2027-01-02

## Context and Problem Statement

Following `ADR-0023` (`v3.9.1`/`v3.9.2`), full-ecosystem finalization required manifesting the owner's `404` starred repositories for anti-slop UI design, editorial architecture diagramming, codebase knowledge graphs, and vector illustration across every runtime (`Claude Code`, `Antigravity`, `Codex`, `OpenCode`, `DSH`, `Pi`), while aligning with `sota-compounding-lab` `ADR-0012` (`0.15x` probation Empirical-Bayes throttle), `sota-dynamic-trail-c` `ADR-0016` (Dec-6 `23/5` SIP shadow readiness), and live simultaneous Dual Native `TradingView.app` + `TradingView.exe` coexistence.

## Decision Outcome

1. **Manifest the 24-Repo Starred Visual, Diagram, Knowledge-Graph & Illustration Atlas (`sota-starred-visual-craft.v1`):**
   - Ship `.agents/skills/sota-visual-diagram-craft/SKILL.md` and enrich `UPSTREAM.md` + `SOTA_ECOSYSTEM_MANIFEST.json` (`manifestVersion = "3.9.3"`) across five craft pillars: Editorial Diagramming & C4 (`archify`, `diagram-design`, `likec4`, `obsidian-skills`), Pedagogical Knowledge Graphs (`graphify`, `Understand-Anything`, `codegraph`, `codebase-memory-mcp`, `code-review-graph`), Anti-Slop Design Systems (`ui-ux-pro-max-skill`, `taste-skill`, `impeccable`, `hallmark`, `astryx`, `awesome-claude-design`), Vector Illustration & Quant Visuals (`openpencil`, `artcraft`, `openmotion`, `perspective`, `lightweight-charts`), and Visual Plan/BLUF Review (`plannotator`, `humanizer`, `i-have-adhd`).

## Alternatives Considered

- **Ad-hoc unpinned visual/diagram generation without anti-slop tokens or C4/AST graph grounding:** Rejected; deterministic skill contracts eliminate generic AI boilerplate across all peer runtimes.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` -> `24 GitHub-evidenced ADRs valid, 0 drift`
- `pytest -q` -> `passed`
- `python3 scripts/merge_gate.py && gitleaks git --log-opts=origin/main..HEAD` -> `[AGY-MERGE-GATE PASS]`, `0` leaks
