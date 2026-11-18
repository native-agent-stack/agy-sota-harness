# ADR-0005: L4 Converged 16 Cross-Peer Skills & 8 SHA-Pinned Vendored Scientific/Security Skills

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `L4` Converged Skills & Progressive Disclosure
- **Evidence Grade:** E4 (Zero-Broken-Symlink & SHA-Pin Sync Verified)
- **GitHub Evidence:** https://github.com/K-Dense-AI/scientific-agent-skills (`ec59a29a03d5c40f73ab40878df04860bc00e876`), https://github.com/cloudflare/security-audit-skill (`c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`), https://github.com/obra/superpowers (`22f0b463e7a5`), https://github.com/OthmanAdi/planning-with-files (`51bf62def62d`), https://github.com/karpathy/autoresearch (`7bddd056dfd0`)
- **Revisit Trigger:** 2027-01-01 or upstream skill pin bump in `.agents/UPSTREAM_SKILL_PINS.json`

## Context and Problem Statement

Keeping global `GEMINI.md`, `CLAUDE.md`, and `AGENTS.md` lean (`<= 45` lines) requires moving domain-heavy procedures (TDD, AST codemods, dimensional/property testing, microstructure/SEC EDGAR catalysts, quantitative statistical gates, multi-agent councils, Orca orchestration, and 5-phase SOTA workflows) into progressive-disclosure `SKILL.md` modules loaded only when relevant—and shared identically across Antigravity, Claude Code, and Codex.

## Decision Outcome

1. **16 Canonical Cross-Peer Skills (`~/.agents/skills/*`):** Maintain one canonical source directory (`~/.agents/skills/`) symlink-mounted into `~/.gemini/config/skills/`, `~/.claude/skills/`, and `~/.codex/skills/` (`autoresearch-loop`, `council-of-high-intelligence`, `microstructure-and-sec-catalyst-lab`, `orca-cli`, `orchestration`, `planning-with-files`, `sota-ast-codemod`, `sota-dimensional-and-property-invariants`, `sota-mover-ranker`, `sota-peer-bus-and-handover`, `sota-quant-research-protocol`, `sota-skillopt-self-evolution`, `sota-spec-and-adr-gate`, `sota-taste-anti-slop`, `sota-tdd-superpowers`, `sota-verification-and-security-gate`, `sota-workflow`).
2. **8 SHA-Pinned Vendored Scientific & Security Audit Skills (`.agents/UPSTREAM_SKILL_PINS.json`):** Deterministically sync `polars`, `statsmodels`, `statistical-analysis`, `hypothesis-generation`, `exploratory-data-analysis`, `scikit-learn`, `aeon` (`K-Dense-AI/scientific-agent-skills@ec59a29a`), and `security-audit` (`cloudflare/security-audit-skill@c1c8a8c1`) via `scripts/sync_vendored_skills.py`.

## Alternatives Considered

1. **Embedding all quant/TDD/security checklists inline in global `GEMINI.md`:** Rejected — violates the `<= 45`-line context-efficiency ceiling and degrades adherence on unrelated tasks.
2. **Unpinned `npx skills add` downloads at runtime:** Rejected — introduces supply-chain mutation risk and network nondeterminism.

## Verification Witness

- `harness/run_probes.py` `L4` verifies `>= 16` canonical skills mounted `16/16/16` across AGY, Claude Code, and Codex, `>= 8` vendored skills, and `0` drift in `docs/adr/CATALOG.md`.
- `~/.agents/bin/sota-doctor` `L2` verifies `0` broken symlinks across `~/.gemini/`, `~/.claude/`, and `~/.codex/`.
