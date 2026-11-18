# Upstream Source-of-Truth Register (`L0–L12` × `T0–T8` × `P0–P5` Peers)

Every tool, library, skill, AST rule, sandbox policy, and orchestrator pattern in `agy-sota-harness` is anchored to a maintained upstream release or 40-character Git commit verified on **2026-11-17**. Enforced fail-closed by `scripts/merge_gate.py` against `upstream-map.toml` and `~/Documents/upstream/PINS.md`.

---

## Part I — Agentic Harness & Multi-Peer Layers (`L0–L12`, Starred + Beyond)

| Key | Layer | Upstream Repository | Verified Pin / Commit | License | Role in Converged Ecosystem |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `cpython-stdlib` | **L0** | https://github.com/python/cpython | `3.14.10` | PSF-2.0 | Zero-dependency JSON-RPC MCP, SQLite WAL/FTS5, AST & hook runtime |
| `mise` | **L0** | https://github.com/jdx/mise | `2026.11.6` | MIT | Reproducible polyglot CLI provisioning & `mise.lock` provenance |
| `uv` | **L0** | https://github.com/astral-sh/uv | `0.13.7` | Apache-2.0 / MIT | Deterministic Python lockfile (`uv.lock`) & tool isolated shims |
| `ruff` | **L0/L1** | https://github.com/astral-sh/ruff | `0.17.5` | MIT | Sub-50ms Rust Python linter (`PostToolUse` + `Stop` self-healing gate) |
| `ty` | **L0/L8** | https://github.com/astral-sh/ty | `0.0.105` | MIT | Rust static type checker for hooks, MCP servers, and invariant modules |
| `ast-grep` | **L0/L5** | https://github.com/ast-grep/ast-grep | `0.51.3` | MIT | Deterministic structural AST search & YAML rule-pack gate (`sota_ast_lint_audit`) |
| `antigravity-sdk` | **L1/L12** | https://github.com/google-antigravity/antigravity-sdk-python | `agy 1.5.3` | Apache-2.0 | Antigravity 2.0 App, `agy` CLI, native `hooks.json`, `run_workflow`, `swarm` & Sidecars |
| `orca` | **L1/L4** | https://github.com/stablyai/orca | `1.4.255` | Bundled | Multi-agent worktree cockpit (`orca.yaml`), `orca-cli`, and heterogeneous dispatch |
| `superpowers` | **L2** | https://github.com/obra/superpowers | `v7.0.2` (`22f0b463e7a5`) | MIT | Red-Green-Refactor TDD, systematic root-cause debugging & worktree discipline |
| `spec-kit` | **L2** | https://github.com/github/spec-kit | `2026-SOTA` | MIT | Spec-Driven Development (`spec.md` -> `tasks.md`) + ADR contract gate (Beyond-Starred) |
| `planning-with-files` | **L2/L7** | https://github.com/OthmanAdi/planning-with-files | `v3.28.2` (`51bf62def62d`) | MIT | Compaction-proof file state (`plan.md`, `findings.md`, `handover.md`) |
| `autoresearch` | **L2/L12** | https://github.com/karpathy/autoresearch · `uditgoenka/autoresearch` | `v2.3.0` (`7bddd056dfd0`) | MIT | Bounded *Hypothesize -> Pre-Wall Verify -> Falsify -> Keep/Discard* loop |
| `peer-bus-hcom` | **L3/L7** | https://github.com/aannoo/hcom · `codejunkie99/agentic-stack` | `hcom v0.7.31` + `peer_bus.db` WAL | MIT | Real-time cross-terminal push wakeup (`hcom`), atomic peer leases (`PreToolUse`), handovers & `LESSONS.md` |
| `council-tradingagents` | **L4/L12** | https://github.com/TauricResearch/TradingAgents · `0xNyk/council-of-high-intelligence` | `2026-SOTA` | Apache-2.0 / MIT | Stateful Proposer vs. Falsifier vs. Verifier multi-agent deliberation |
| `codebase-memory-graph` | **L5** | https://github.com/DeusData/codebase-memory-mcp · `colbymchenry/codegraph` | `v0.12.1` / `1.6.3` | MIT | Symbol-level AST call-graph & change-aware test impact analysis |
| `scientific-agent-skills` | **L6** | https://github.com/K-Dense-AI/scientific-agent-skills | `ec59a29a03d5c40f73ab40878df04860bc00e876` | MIT | Vendored pinned `polars`, `statsmodels`, `statistical-analysis`, `hypothesis-generation`, `eda`, `sklearn`, `aeon` skills |
| `context-mode` | **L7** | https://github.com/mksglu/context-mode · `rtk-ai/rtk` | `v2.2.1` (`99c5f38b622c`) | Source-Available / MIT | SQLite FTS5 tool-output sandbox achieving 80–98% context byte compression |
| `beads` | **L7** | https://github.com/gastownhall/beads | `v1.3.4` (`7ef2fd05e`) | MIT | Git-native dependency-aware agent task graph (`bd`) |
| `trailofbits-skills` | **L8** | https://github.com/trailofbits/skills | `149d7b21f4067765b82e67029730b42d228ef4b4` | CC-BY-SA-4.0 | Dimensional unit safety (`bps`/`pct`/`ratio`), `fp-check`, sharp-edges & property invariants |
| `hypothesis` | **L8** | https://github.com/HypothesisWorks/hypothesis | `6.170.15` | MPL-2.0 | Stateful & property-based fuzzing of `ADR-0022` stops and dimensional math (Beyond-Starred) |
| `security-audit-skill` | **L8** | https://github.com/cloudflare/security-audit-skill | `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8` | MIT | Multi-phase verified security audit skill |
| `sandbox-runtime` | **L9** | https://github.com/anthropic-experimental/sandbox-runtime | `0.0.83` | Apache-2.0 | macOS Seatbelt (`srt`) kernel network/filesystem confinement (`srt-agy-worker.json`) |
| `gitleaks` | **L9** | https://github.com/gitleaks/gitleaks | `8.30.1` | MIT | Staged secret, `PA...`/`DU...` account ID, and API-key blocker |
| `agentsview-skillopt` | **L10/L12** | https://github.com/microsoft/SkillOpt · `kenn-io/agentsview` · `NousResearch/hermes-agent-self-evolution` | `0.47.0` | MIT | Redacted `transcript.jsonl` friction mining & validation-gated `SKILL.md` evolution |
| `agent-desktop-browser` | **L11** | https://github.com/vercel-labs/agent-desktop · `vercel-labs/agent-browser` | `1.3.1` / `0.43.0` | Apache-2.0 | On-demand macOS `AXUIElement` (`TradingView.app`) & browser verification CLIs |
| `impeccable-taste` | **L6/L12** | https://github.com/pbakaus/impeccable · `Leonxlnx/taste-skill` · `Nutlope/hallmark` · `nextlevelbuilder/ui-ux-pro-max-skill` | `2026-SOTA` | MIT | Anti-AI-slop institutional UI typography, `tabular-nums`, `meta/astryx` tokens & browser visual critique |
| `editorial-diagrams-c4` | **L6/L9** | https://github.com/tt-a1i/archify · `cathrynlavery/diagram-design` · `likec4/likec4` · `obsidianmd/obsidian-skills` | `2026-SOTA` | MIT / Apache-2.0 | Self-contained HTML/SVG/Mermaid/C4 architecture-as-code & spatial JSON Canvas maps |
| `pedagogical-code-graphs` | **L4/L8** | https://github.com/Graphify-Labs/graphify · `Egonex-AI/Understand-Anything` · `tirth8205/code-review-graph` | `2026-SOTA` | MIT | Leiden/Tree-sitter codebase + DuckDB schema knowledge graphs & differential PR blast-radius graphs |
| `vector-illustration-craft` | **L6/L9** | https://github.com/ZSeven-W/openpencil · `storytold/artcraft` · `nexu-io/openmotion` · `backnotprop/plannotator` | `2026-SOTA` | MIT / Apache-2.0 | Concurrent agent vector illustration (`Design-as-Code`), programmable motion & visual plan review |

---

## Part II — Trading System Stack Upstreams (`T0–T8`, Verified in `~/Documents/upstream/`)

| Key | Tier | Upstream Repository | Pin / Tag | Exact Commit SHA | License |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `alpaca-py` | **T1/T2** | https://github.com/alpacahq/alpaca-py | `v0.45.0` | `c42add7c0a7026e2ead3ed64e76f4def2b99fda4` | Apache-2.0 |
| `alpaca-mcp-server` | **T5** | https://github.com/alpacahq/alpaca-mcp-server | `v2.4.1` | `63cc4278d87b31f3ed4efcfaa55624095c6d7be8` | MIT |
| `nautilus_trader` | **T3/T5** | https://github.com/nautechsystems/nautilus_trader | `v2.0.0rc9` | `da6b57aefdd62b44f675e434ffcfefca7f4025dd` | LGPL-3.0+ |
| `nautilus-alpaca` | **T5** | https://github.com/gmatrunich/nautilus-alpaca | commit | `59685d56631b981018a189b5ced1a7000a50bfbd` | Apache-2.0 |
| `polars` | **T1/T2** | https://github.com/pola-rs/polars | `py-2.1.0` | `7f902bd3ffd27ff82d14278a09a295ff2f7aed92` | MIT |
| `duckdb` | **T1** | https://github.com/duckdb/duckdb | `v2.0.0` | `d54cbbe3df17e8e5ce68312f483b4155836112aa` | MIT |
| `edgartools` | **T2** | https://github.com/dgunning/edgartools | `v6.2.0` | `574c2bd15f6c629bceef03b6550ea8ac8abf3473` | MIT |
| `ml4t-diagnostic` | **T4** | https://github.com/ml4t/diagnostic | `v0.2.0` | `19e76072e64a18c9ba56130e4a7bcc0bc871f57e` | MIT |
| `skfolio` | **T4** | https://github.com/skfolio/skfolio | `v1.12.7` | `90e3fb907fab39d244d899f3caf4e9676889309c` | BSD-3-Clause |
| `hftbacktest` | **T3** | https://github.com/nkaz001/hftbacktest | commit | `5f3ec40b2afb764e0fea112f941ed85523ef4e88` | MIT |
| `ib_async` | **T5** | https://github.com/ib-api-reloaded/ib_async | `v2.1.0` | `ab629f34c1823ea4c1542f32f07377208a86bdfd` | BSD-3-Clause |
| `perspective` | **T8** | https://github.com/finos/perspective | `v5.9.2` | `0264ec13cd28ef4a2a136c8ef021c3c112bc8990` | Apache-2.0 |
| `lightweight-charts` | **T8** | https://github.com/tradingview/lightweight-charts | commit | `c29c51e1e5bc61981da5832c97797cb8283d120f` | Apache-2.0 |
| `quantstats` | **T6/T8** | https://github.com/ranaroussi/quantstats | commit | `d1a214fb906e76f974f45cdccf923b601c67a756` | Apache-2.0 |
| `vectorbt` | **T4** | https://github.com/polakowo/vectorbt | `v1.2.0` | `a52a984b631624bb9daf41cb19f532fe559cf0ef` | Apache-2.0 |
| `pandera` | **T1** | https://github.com/unionai-oss/pandera | `v0.35.0` | `02b375ab43f39f8c5c5108695c1791fa04f99a26` | MIT |
| `exchange_calendars` | **T1/T3** | https://github.com/gerrymanoim/exchange_calendars | `4.13.2` | `dbe38b1f6887434bbdd1a7d2df6ff8f1742a048a` | Apache-2.0 |
| `statsmodels` | **T4** | https://github.com/statsmodels/statsmodels | `v0.15.0` | `278ff9950636cdd4939b4055e339a8e681d79cab` | BSD-3-Clause |
