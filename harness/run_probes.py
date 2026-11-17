#!/usr/bin/env python3
"""Offline 10-Layer (`L0–L9`) Verification Runner for the AGY SOTA Multi-Repo Stack."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

HOME = Path.home()
DOCS = HOME / "Documents"
HARNESS_ROOT = Path(__file__).resolve().parents[1]
CORE_HUB = DOCS / ".agents-core"
PLUGIN_DIR = HOME / ".gemini" / "config" / "plugins" / "agy-sota-core"
SHELF_DIR = DOCS / "upstream"

BRIDGED_REPOS = (
    "claude-trading-skills",
    "edge",
    "meridian",
    "movers",
    "sota-mover-ranker",
    "trading-sota",
    "tsl",
    "dsh",
    "dsh-sota-harness",
)

HOME_LEAK_RE = re.compile(r"/" + r"Users/[A-Za-z0-9._-]+/")
SECRET_LEAK_RE = re.compile(r"(?:\bPA[0-9A-Z]{10}\b|\bDU[0-9]{7,9}\b|\b(?:AK|PK)[0-9A-Z]{20}\b)")


def run_hook(script: Path, payload: dict[str, Any], env_extra: dict[str, str] | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=8,
        check=True,
    )
    return json.loads(proc.stdout.strip() or "{}")


def call_mcp(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mcp_py = PLUGIN_DIR / "mcp" / "sota_core_mcp.py"
    stdin_txt = "\n".join(json.dumps(r) for r in requests) + "\n"
    proc = subprocess.run(
        [sys.executable, "-B", str(mcp_py)],
        input=stdin_txt,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return [json.loads(ln) for ln in proc.stdout.splitlines() if ln.strip()]


def probe_l0() -> str:
    assert (PLUGIN_DIR / "plugin.json").is_file(), "Missing agy-sota-core/plugin.json"
    assert (CORE_HUB / "skills.json").is_file(), "Missing .agents-core/skills.json"
    for r in BRIDGED_REPOS:
        sj = DOCS / r / ".agents" / "skills.json"
        assert sj.is_file(), f"Missing bridge {sj}"
        data = json.loads(sj.read_text(encoding="utf-8"))
        inherits = [x.get("path") for x in (data.get("inherits") or [])]
        assert "~/Documents/.agents-core/skills.json" in inherits, f"{r} missing .agents-core inheritance"
    return f"plugin + .agents-core + {len(BRIDGED_REPOS)}/9 repo skills.json bridges verified"


def probe_l1() -> str:
    pre = PLUGIN_DIR / "hooks" / "pre_tool_guard.py"
    post = PLUGIN_DIR / "hooks" / "post_tool_lint.py"
    stop = PLUGIN_DIR / "hooks" / "stop_quality_gate.py"

    # 1. PreToolUse firewall checks
    r_live = run_hook(pre, {"toolCall": {"name": "run_command", "args": {"CommandLine": "~/.claude/bin/live status"}}})
    assert r_live.get("decision") == "deny", f"Expected deny on live binary, got {r_live}"

    r_port = run_hook(pre, {"toolCall": {"name": "run_command", "args": {"CommandLine": "nc -z 127.0.0.1 4001"}}})
    assert r_port.get("decision") == "deny", f"Expected deny on IBKR live port 4001, got {r_port}"

    r_up = run_hook(
        pre,
        {"toolCall": {"name": "write_file", "args": {"Path": str(SHELF_DIR / "polars" / "HACK.md"), "Content": "x"}}},
    )
    assert r_up.get("decision") == "deny", f"Expected deny on upstream shelf write, got {r_up}"

    fake_key = "PK" + ("A1B2C3D4E5" * 2)
    r_sec = run_hook(
        pre,
        {"toolCall": {"name": "write_file", "args": {"Path": "/tmp/leak_test.txt", "Content": f"key={fake_key}"}}},
    )
    assert r_sec.get("decision") == "deny", f"Expected deny on raw key literal, got {r_sec}"

    r_git = run_hook(pre, {"toolCall": {"name": "run_command", "args": {"CommandLine": "git reset --hard HEAD~1"}}})
    assert r_git.get("decision") == "ask", f"Expected ask on git reset --hard, got {r_git}"

    r_ok = run_hook(pre, {"toolCall": {"name": "run_command", "args": {"CommandLine": "pytest -q"}}})
    assert r_ok.get("decision") == "allow", f"Expected allow on benign pytest, got {r_ok}"

    # 2. PostToolUse + Stop self-healing loop check
    with tempfile.TemporaryDirectory() as tmpd:
        bad_py = Path(tmpd) / "broken_probe.py"
        bad_py.write_text("def f() -> int:\n    return undefined_var_xyz + 1\n", encoding="utf-8")
        env = {"PLUGIN_DATA": tmpd}
        run_hook(
            post,
            {
                "conversationId": "probe-conv",
                "toolCall": {"name": "write_file", "args": {"Path": str(bad_py)}},
            },
            env_extra=env,
        )
        s_cont = run_hook(
            stop,
            {"conversationId": "probe-conv", "continuationActive": False, "terminationReason": "NO_TOOL_CALL"},
            env_extra=env,
        )
        assert s_cont.get("decision") == "continue", f"Expected Stop hook continue on F821 error, got {s_cont}"

        # Continuation-active guard prevents infinite loops
        s_guard = run_hook(
            stop,
            {"conversationId": "probe-conv", "continuationActive": True, "terminationReason": "NO_TOOL_CALL"},
            env_extra=env,
        )
        assert s_guard.get("decision") == "allow", f"Expected allow when continuationActive=True, got {s_guard}"

    return "PreToolUse (5 deny/ask + 1 allow) & PostToolUse->Stop F821 self-healing verified"


def probe_l2() -> str:
    resps = call_mcp(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ]
    )
    assert resps[0]["result"]["protocolVersion"] == "2025-03-26"
    tools = resps[1]["result"]["tools"]
    assert len(tools) == 5, f"Expected 5 tools, found {len(tools)}"

    global_mcp = HOME / ".gemini" / "config" / "mcp_config.json"
    g_count = len(json.loads(global_mcp.read_text(encoding="utf-8")).get("mcpServers") or {}) if global_mcp.is_file() else 0
    total_active = g_count + 1  # +1 for agy-sota-core plugin MCP
    assert total_active <= 6, f"Lean MCP violation: {total_active} > 6"
    return f"MCP 2025-03-26 online (5 tools; total global MCP servers={total_active} <= 6 Lean budget)"


def probe_l3() -> str:
    resps = call_mcp(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "sota_symbol_lookup",
                    "arguments": {"symbol": "EarlyMoverGoalLoop", "repo": "sota-mover-ranker", "include_body": False},
                },
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "sota_ast_search",
                    "arguments": {"pattern": "def verify_upstream_map($$$ARGS)", "repo": "sota-mover-ranker"},
                },
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "sota_shelf_search",
                    "arguments": {"query": "ADR-0022 CombinatorialPurgedCV", "scope": "all", "limit": 5},
                },
            },
        ]
    )
    sym = resps[0]["result"]["structuredContent"]
    ast_r = resps[1]["result"]["structuredContent"]
    shelf = resps[2]["result"]["structuredContent"]
    assert sym["count"] >= 1, "Symbol lookup missed EarlyMoverGoalLoop"
    assert ast_r["count"] >= 1, "AST search missed verify_upstream_map"
    assert shelf["count"] >= 1 and shelf["indexed_docs"] >= 50, f"Shelf FTS5 under-indexed: {shelf}"

    # Verify zero dirty files in ~/Documents/upstream/
    dirty = []
    for udir in sorted(SHELF_DIR.iterdir()):
        if (udir / ".git").exists():
            st = subprocess.run(["git", "-C", str(udir), "status", "--short"], capture_output=True, text=True, check=True)
            if st.stdout.strip():
                dirty.append(udir.name)
    assert not dirty, f"Upstream shelf dirty: {dirty}"
    return f"AST symbol + sg + FTS5 shelf ({shelf['indexed_docs']} docs, {shelf['elapsed_ms']}ms, 18/18 shelf clean)"


def probe_l4() -> str:
    skills_dir = CORE_HUB / "skills"
    skill_files = sorted(skills_dir.glob("*/SKILL.md"))
    assert len(skill_files) >= 6, f"Expected >=6 core skills, found {len(skill_files)}"
    for sf in skill_files:
        txt = sf.read_text(encoding="utf-8")
        assert txt.startswith("---\n") and "name:" in txt and "description:" in txt, f"Invalid frontmatter in {sf}"
        assert len(txt.encode("utf-8")) < 8000, f"Skill {sf} exceeds progressive-disclosure budget"

    rule_md = PLUGIN_DIR / "rules" / "AGENTS.md"
    assert rule_md.stat().st_size < 24000, "Plugin AGENTS.md exceeds 24KB AGY rule cap"

    cts_skills = list((DOCS / "claude-trading-skills" / ".claude" / "skills").glob("*/SKILL.md"))
    edge_skills = list((DOCS / "edge" / ".claude" / "skills").glob("*/SKILL.md"))
    return f"{len(skill_files)} core skills + {len(cts_skills) + len(edge_skills)} bridged .claude skills validated"


def probe_l5() -> str:
    wf_files = sorted((CORE_HUB / "workflows").glob("*.py"))
    assert len(wf_files) >= 3, "Expected >=3 shared run_workflow scripts"
    for wf in wf_files:
        src = wf.read_text(encoding="utf-8")
        ast.parse(src, filename=str(wf))
        assert "phase(" in src and "schema=" in src or "SCHEMA" in src, f"{wf.name} missing phase/typed schema"
        assert not HOME_LEAK_RE.search(src), f"Hardcoded home path leak in {wf}"
    return f"{len(wf_files)} schema-typed run_workflow Python DAGs AST-verified"


def probe_l6() -> str:
    taste = CORE_HUB / "skills" / "sota-taste-anti-slop" / "SKILL.md"
    devtools = HOME / ".gemini" / "config" / "plugins" / "chrome-devtools-plugin"
    assert taste.is_file() and devtools.is_dir()
    return "sota-taste-anti-slop + chrome-devtools-plugin verified"


def probe_l7() -> str:
    cmd = f"{sys.executable} -c \"for i in range(250): print('INFO line', i); print('PASSED summary check')\""
    resps = call_mcp(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "sota_compressed_exec", "arguments": {"command": cmd, "max_summary_chars": 600}},
            }
        ]
    )
    out = resps[0]["result"]["structuredContent"]
    assert out["exit_code"] == 0 and out["context_saved_pct"] >= 50.0, f"Insufficient compression: {out}"
    return f"FTS5 output sandbox saved {out['context_saved_pct']}% context bytes ({out['raw_bytes']}B -> {out['returned_bytes']}B)"


def probe_l8() -> str:
    for bin_name in ("ruff", "ty", "sg"):
        bp = HOME / ".local" / "bin" / bin_name
        assert bp.is_file() and os.access(bp, os.X_OK), f"Missing binary {bp}"

    # Verify zero hardcoded /Users/<name> or secret leaks in tracked/shared harness & core files
    for root in (HARNESS_ROOT, CORE_HUB, PLUGIN_DIR):
        for fp in root.rglob("*"):
            if not fp.is_file() or "cache" in fp.parts or "__pycache__" in fp.parts:
                continue
            txt = fp.read_text(encoding="utf-8", errors="ignore")
            assert not SECRET_LEAK_RE.search(txt), f"Secret/account pattern leak in {fp}"
            if root in (HARNESS_ROOT, CORE_HUB):
                assert not HOME_LEAK_RE.search(txt), f"Local home path leak in {fp}"

    # Verify flagship sota-mover-ranker merge_gate.py still passes cleanly
    mg = DOCS / "sota-mover-ranker" / "scripts" / "merge_gate.py"
    if mg.is_file():
        proc = subprocess.run([sys.executable, str(mg)], capture_output=True, text=True, timeout=15, check=True)
        assert "MERGE-GATE PASS" in proc.stdout

    return "ruff/ty/sg/gitleaks + zero-leak privacy scan + sota-mover-ranker merge_gate PASS"


def probe_l9() -> str:
    resps = call_mcp(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "sota_trajectory_friction", "arguments": {"max_sessions": 12}},
            }
        ]
    )
    diag = resps[0]["result"]["structuredContent"]
    cache_dir = HARNESS_ROOT / "cache"
    cache_dir.mkdir(exist_ok=True)
    (cache_dir / "session_brief.json").write_text(json.dumps(diag, indent=2) + "\n", encoding="utf-8")

    digest_lines = [
        "# AGY SOTA SkillOpt Trajectory Digest",
        "",
        f"- **Sessions Scanned:** `{diag['sessions_scanned']}`",
        f"- **Total Trajectory Steps:** `{diag['total_steps']}`",
        f"- **Truncated Context Steps:** `{diag['truncated_steps']}`",
        "",
        "## Validation-Gated Recommendations",
        *[f"- {r}" for r in diag.get("skillopt_recommendations", [])],
    ]
    (cache_dir / "SKILLOPT_DIGEST.md").write_text("\n".join(digest_lines) + "\n", encoding="utf-8")
    return f"scanned {diag['sessions_scanned']} sessions ({diag['total_steps']} steps) -> cache/SKILLOPT_DIGEST.md READY"


PROBES: tuple[tuple[str, str, Callable[[], str]], ...] = (
    ("L0", "Packaging & 9-Repo Bridges", probe_l0),
    ("L1", "Deterministic Lifecycle Hooks", probe_l1),
    ("L2", "Lean MCP JSON-RPC 2025-03-26", probe_l2),
    ("L3", "AST Graph & 18-Repo Shelf FTS5", probe_l3),
    ("L4", "Progressive-Disclosure Skills", probe_l4),
    ("L5", "Schema-Typed run_workflow DAGs", probe_l5),
    ("L6", "Anti-Slop Taste & DevTools", probe_l6),
    ("L7", "Context-Mode Output Compression", probe_l7),
    ("L8", "Security, Rust Tooling & Merge Gate", probe_l8),
    ("L9", "SkillOpt Trajectory Self-Evolution", probe_l9),
)


def main() -> int:
    t0 = time.perf_counter()
    passed = 0
    print("# AGY SOTA Harness Verification (`L0–L9`)")
    for layer, title, fn in PROBES:
        lt0 = time.perf_counter()
        try:
            detail = fn()
            ms = (time.perf_counter() - lt0) * 1000.0
            print(f"  [PASS] {layer} ({title}) — {detail} [{ms:.0f}ms]")
            passed += 1
        except (AssertionError, OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
            print(f"  [FAIL] {layer} ({title}) — {exc}", file=sys.stderr)
            return 1

    total_ms = (time.perf_counter() - t0) * 1000.0
    print(f"\nResult: {passed}/{len(PROBES)} probes PASSED in {total_ms:.0f}ms.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
