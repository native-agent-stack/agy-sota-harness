#!/usr/bin/env python3
"""Offline 13-Layer (`L0–L12`) Verification Runner for the Full-Landscape AGY & Multi-Peer SOTA Stack."""

from __future__ import annotations

import ast
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

HOME = Path.home()
DOCS = HOME / "Documents"
CANON = HOME / "canon"
HARNESS_ROOT = Path(__file__).resolve().parents[1]
CORE_HUB = DOCS / ".agents-core"
AGENTS_ROOT = HOME / ".agents"
PLUGIN_DIR = HOME / ".gemini" / "config" / "plugins" / "agy-sota-core"
SHELF_DIR = DOCS / "upstream"

BRIDGED_DOCS_REPOS = (
    "astrolabe",
    "cc-sota-harness",
    "claude-trading-skills",
    "dsh",
    "dsh-sota-harness",
    "meridian",
    "native-agent-stack",
    "sota-compounding-lab",
    "sota-dynamic-trail-c",
    "sota-harness-foundation",
    "sota-mover-ranker",
    "sota-multi-model-workflows",
    "sota-private-vault",
    "sota-upstream-shelf-lock",
    "trading-sota",
    "tsl",
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
    for req in (
        "mise.toml",
        "pyproject.toml",
        "orca.yaml",
        "UPSTREAM.md",
        "upstream-map.toml",
        "SOTA_ECOSYSTEM_MANIFEST.json",
    ):
        assert (HARNESS_ROOT / req).is_file(), f"Missing {req}"
    for r in BRIDGED_DOCS_REPOS:
        sj = DOCS / r / ".agents" / "skills.json"
        assert sj.is_file(), f"Missing bridge {sj}"
    if CANON.is_dir():
        assert (CANON / ".agents" / "skills.json").is_file(), "Missing ~/canon/.agents/skills.json bridge"
    orca_repos = sorted(p.name for p in DOCS.iterdir() if p.is_dir() and (p / "orca.yaml").is_file())
    assert len(orca_repos) >= 11, (
        f"Expected >=11 ~/Documents repos with orca.yaml, found {len(orca_repos)}: {orca_repos}"
    )
    return (
        f"lockfiles + {len(orca_repos)} orca.yaml workspace recipes + "
        f"{len(BRIDGED_DOCS_REPOS) + (1 if CANON.is_dir() else 0)} bridged repos verified"
    )


def probe_l1() -> str:
    pre = PLUGIN_DIR / "hooks" / "pre_tool_guard.py"
    post = PLUGIN_DIR / "hooks" / "post_tool_lint.py"
    stop = PLUGIN_DIR / "hooks" / "stop_quality_gate.py"

    assert (
        run_hook(pre, {"toolCall": {"name": "run_command", "args": {"CommandLine": "~/.claude/bin/live status"}}})[
            "decision"
        ]
        == "deny"
    )
    assert (
        run_hook(
            pre,
            {
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "curl https://api.alpaca.markets/v2/account"},
                }
            },
        )["decision"]
        == "deny"
    )
    assert (
        run_hook(pre, {"toolCall": {"name": "run_command", "args": {"CommandLine": "nc -z 127.0.0.1 4001"}}})[
            "decision"
        ]
        == "deny"
    )
    assert (
        run_hook(
            pre,
            {"toolCall": {"name": "write_file", "args": {"Path": str(SHELF_DIR / "polars" / "X.md"), "Content": "x"}}},
        )["decision"]
        == "deny"
    )

    # Verify cross-peer SQLite WAL lease collision guard inside PreToolUse
    with tempfile.TemporaryDirectory() as tmpd:
        fake_bus = Path(tmpd) / "peer_bus.db"
        conn = sqlite3.connect(str(fake_bus))
        conn.execute(
            "CREATE TABLE peer_leases (lease_key TEXT PRIMARY KEY, repo TEXT, paths_json TEXT, agent_family TEXT, session_id TEXT, intent TEXT, claimed_at REAL, expires_at REAL)"
        )
        conn.execute(
            "INSERT INTO peer_leases VALUES ('k1', 'meridian', '[\"*\"]', 'claude', 'other-peer-999', 'refactoring engine', ?, ?)",
            (time.time(), time.time() + 600),
        )
        conn.commit()
        conn.close()

        r_lease = run_hook(
            pre,
            {
                "conversationId": "my-agy-session",
                "toolCall": {
                    "name": "edit_file",
                    "args": {"Path": str(DOCS / "meridian" / "AGENTS.md"), "Replacement": "x"},
                },
            },
            env_extra={"SOTA_PEER_BUS_DB": str(fake_bus)},
        )
        assert r_lease.get("decision") == "ask", f"Expected ask on active peer lease collision, got {r_lease}"

        # PostToolUse + Stop self-healing check
        bad_py = Path(tmpd) / "broken_probe.py"
        bad_py.write_text("def f() -> int:\n    return undefined_var_xyz + 1\n", encoding="utf-8")
        env = {"PLUGIN_DATA": tmpd}
        run_hook(
            post,
            {"conversationId": "c1", "toolCall": {"name": "write_file", "args": {"Path": str(bad_py)}}},
            env_extra=env,
        )
        assert (
            run_hook(
                stop,
                {"conversationId": "c1", "continuationActive": False, "terminationReason": "NO_TOOL_CALL"},
                env_extra=env,
            )["decision"]
            == "continue"
        )

    return "PreToolUse (live-bin, api.alpaca.markets, :4001, shelf, peer-lease ask) & PostToolUse->Stop verified"


def probe_l2() -> str:
    resps = call_mcp(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ]
    )
    assert resps[0]["result"]["protocolVersion"] == "2025-03-26"
    tools = resps[1]["result"]["tools"]
    assert len(tools) == 7, f"Expected 7 tools in agy-sota-core MCP, found {len(tools)}"

    global_mcp = HOME / ".gemini" / "config" / "mcp_config.json"
    g_count = (
        len(json.loads(global_mcp.read_text(encoding="utf-8")).get("mcpServers") or {}) if global_mcp.is_file() else 0
    )
    # 2 in mcp_config.json + agy-sota-core + sota-peer-bus = 4 active MCP servers (<= 6 Lean budget)
    total_active = g_count + 2
    assert total_active <= 6, f"Lean MCP violation: {total_active} > 6"
    return f"MCP 2025-03-26 online (7 core tools; total active MCP servers={total_active} <= 6 Lean budget)"


def probe_l3() -> str:
    resps = call_mcp(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "sota_symbol_lookup",
                    "arguments": {"symbol": "validate_adr0022_stop", "repo": "agy-sota-harness", "include_body": False},
                },
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "sota_shelf_search",
                    "arguments": {"query": "ADR-0022 CombinatorialPurgedCV", "scope": "all", "limit": 5},
                },
            },
        ]
    )
    sym = resps[0]["result"]["structuredContent"]
    shelf = resps[1]["result"]["structuredContent"]
    assert sym["count"] >= 1, "Symbol lookup missed validate_adr0022_stop"
    assert shelf["count"] >= 1 and shelf["indexed_docs"] >= 50, f"Shelf FTS5 under-indexed: {shelf}"
    return f"AST symbol + FTS5 shelf ({shelf['indexed_docs']} docs, {shelf['elapsed_ms']}ms)"


def probe_l4() -> str:
    canonical = sorted(p.name for p in (AGENTS_ROOT / "skills").iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    assert len(canonical) >= 16, f"Expected >=16 canonical ~/.agents/skills, found {len(canonical)}"
    for peer_dir in (HOME / ".gemini" / "config" / "skills", HOME / ".claude" / "skills", HOME / ".codex" / "skills"):
        mounted = sum(1 for s in canonical if (peer_dir / s).exists())
        assert mounted == len(canonical), f"Peer {peer_dir} only mounted {mounted}/{len(canonical)} canonical skills"

    v_dir = HARNESS_ROOT / ".agents" / "skills"
    vendored = (
        sorted(p.name for p in v_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()) if v_dir.is_dir() else []
    )
    if len(vendored) < 8 and (DOCS / "agy-sota-harness" / ".agents" / "skills").is_dir():
        fb = DOCS / "agy-sota-harness" / ".agents" / "skills"
        vendored = sorted(p.name for p in fb.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    assert len(vendored) >= 8, f"Expected >=8 vendored scientific/security skills, found {len(vendored)}"
    cat_p = subprocess.run(
        [sys.executable, str(HARNESS_ROOT / "scripts" / "architecture_catalog.py"), "--check"],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    assert "0 drift" in cat_p.stdout, f"ADR catalog drift: {cat_p.stdout}"
    adr_total = len(list((HARNESS_ROOT / "docs" / "adr").glob("ADR-[0-9][0-9][0-9][0-9]-*.md")))
    return (
        f"{len(canonical)} canonical skills converged across AGY+Claude+Codex + "
        f"{len(vendored)} vendored skills + {adr_total} GitHub-evidenced MADR 4.0 ADRs"
    )


def probe_l5() -> str:
    wf_files = sorted((HARNESS_ROOT / "src" / "agy_sota" / "workflows").glob("*.py"))
    assert len(wf_files) >= 6, "Expected >=6 full-landscape run_workflow DAGs"
    for wf in wf_files:
        src = wf.read_text(encoding="utf-8")
        ast.parse(src, filename=str(wf))
        assert "phase(" in src and "SCHEMA" in src, f"{wf.name} missing phase/typed schema"
        assert not HOME_LEAK_RE.search(src), f"Hardcoded home path leak in {wf}"
        if "__file__" in src:
            assert '"__file__" in globals()' in src or "'__file__' in globals()" in src, (
                f"{wf.name} uses unguarded __file__ (fails inside <workflow> globals)"
            )
        assert "load_research_convergence_context" in src and "sota-research-feeds.v2" in src, (
            f"{wf.name} missing explicit load_research_convergence_context / sota-research-feeds.v2 binding"
        )
        assert "verify_workflow_research_convergence" in src, (
            f"{wf.name} missing verify_workflow_research_convergence gate"
        )
        assert "PHILOSOPHY_ONLY" in src, f"{wf.name} missing ADR-0004 PHILOSOPHY_ONLY sibling-repo rule"
    return f"{len(wf_files)} schema-typed AGY run_workflow pipelines AST + Research-Convergence verified"


def probe_l6() -> str:
    taste = AGENTS_ROOT / "skills" / "sota-taste-anti-slop" / "SKILL.md"
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
    assert out["exit_code"] == 0 and out["context_saved_pct"] >= 50.0
    assert (AGENTS_ROOT / "bin" / "sota-bus").is_file() and (AGENTS_ROOT / "bin" / "sota-core").is_file()
    return f"FTS5 output sandbox ({out['context_saved_pct']}% saved) + sota-bus & sota-core CLIs verified"


def probe_l8() -> str:
    # Verify ast-grep YAML rule pack catches intentional synthetic violations and passes clean src/
    with tempfile.TemporaryDirectory() as tmpd:
        bad = Path(tmpd) / "bad_trading.py"
        bad.write_text(
            "from datetime import datetime\nfrom alpaca.trading import TradingClient\nib.connect('127.0.0.1', 4001)\nt = datetime.now()\n",
            encoding="utf-8",
        )
        resps = call_mcp(
            [
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": "sota_ast_lint_audit", "arguments": {"target": str(bad)}},
                },
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "sota_ast_lint_audit", "arguments": {"target": str(HARNESS_ROOT / "src")}},
                },
            ]
        )
        bad_audit = resps[0]["result"]["structuredContent"]
        clean_audit = resps[1]["result"]["structuredContent"]
        rule_ids = {f["rule_id"] for f in bad_audit["findings"]}
        assert {"no-live-alpaca-trading-import", "no-live-ibkr-port", "no-naive-datetime-now"}.issubset(rule_ids), (
            f"Missed AST rules: {rule_ids}"
        )
        assert clean_audit["clean"] is True, f"Unexpected AST findings in src/: {clean_audit}"
    return "4 ast-grep YAML rules caught synthetic live/datetime violations & passed src/ cleanly"


def probe_l9() -> str:
    srt_policy = json.loads((HARNESS_ROOT / "policies" / "srt-agy-worker.json").read_text(encoding="utf-8"))
    assert "api.alpaca.markets" in srt_policy["network"]["deniedDomains"]
    assert "~/Documents/upstream" in srt_policy["filesystem"]["denyWrite"]
    assert (HARNESS_ROOT / ".gitleaks.toml").is_file()

    mg_self = HARNESS_ROOT / "scripts" / "merge_gate.py"
    p_self = subprocess.run([sys.executable, str(mg_self)], capture_output=True, text=True, timeout=15, check=True)
    assert "AGY-MERGE-GATE PASS" in p_self.stdout

    mg_ranker = DOCS / "sota-mover-ranker" / "scripts" / "merge_gate.py"
    if mg_ranker.is_file():
        p_rk = subprocess.run([sys.executable, str(mg_ranker)], capture_output=True, text=True, timeout=15)
        if p_rk.returncode == 0:
            assert "MERGE-GATE PASS" in p_rk.stdout
        else:
            import sqlite3
            import time as _time

            bus_db = AGENTS_ROOT / "bus" / "peer_bus.db"
            has_peer_lease = False
            if bus_db.is_file():
                with sqlite3.connect(str(bus_db)) as conn:
                    row = conn.execute(
                        "SELECT 1 FROM peer_leases WHERE repo='sota-mover-ranker' AND expires_at > ? LIMIT 1",
                        (_time.time(),),
                    ).fetchone()
                    has_peer_lease = row is not None
            if not has_peer_lease:
                raise subprocess.CalledProcessError(p_rk.returncode, p_rk.args, output=p_rk.stdout, stderr=p_rk.stderr)
            with tempfile.TemporaryDirectory() as tmp_rk:
                subprocess.run(
                    f"git -C '{DOCS / 'sota-mover-ranker'}' archive HEAD | tar -x -C '{tmp_rk}'",
                    shell=True,
                    check=True,
                    timeout=15,
                )
                subprocess.run(["git", "-C", tmp_rk, "init", "-q"], check=True, timeout=10)
                subprocess.run(["git", "-C", tmp_rk, "add", "-A"], check=True, timeout=10)
                subprocess.run(
                    [
                        "git",
                        "-C",
                        tmp_rk,
                        "-c",
                        "user.name=sota-probe",
                        "-c",
                        "user.email=sota-probe@users.noreply.github.com",
                        "commit",
                        "-q",
                        "-m",
                        "head-archive",
                    ],
                    check=True,
                    timeout=10,
                )
                p_head = subprocess.run(
                    [sys.executable, str(Path(tmp_rk) / "scripts" / "merge_gate.py")],
                    cwd=tmp_rk,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=True,
                )
                assert "MERGE-GATE PASS" in p_head.stdout

    return "Seatbelt srt policy + .gitleaks.toml + agy-sota-harness & sota-mover-ranker merge gates PASS"


def probe_l10() -> str:
    sidecar = HOME / ".gemini" / "config" / "sidecars" / "sota-early-mover-paper-goal" / "sidecar.json"
    assert sidecar.is_file()
    sc_data = json.loads(sidecar.read_text(encoding="utf-8"))
    grants = (sc_data.get("agent_permissions") or {}).get("access_grants") or []
    assert len(grants) >= 5
    return f"scheduled sidecar + {len(grants)} scoped access_grants verified"


def probe_l11() -> str:
    dirty = []
    count = 0
    for udir in sorted(SHELF_DIR.iterdir()):
        if (udir / ".git").exists():
            count += 1
            st = subprocess.run(
                ["git", "-C", str(udir), "status", "--short"], capture_output=True, text=True, check=True
            )
            if st.stdout.strip():
                dirty.append(udir.name)
    assert count == 18 and not dirty, f"Expected 18 clean upstream clones, got count={count} dirty={dirty}"
    return "18/18 ~/Documents/upstream clones pinned & 100% clean"


def probe_l12() -> str:
    import shutil

    resps = call_mcp(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "sota_ecosystem_convergence", "arguments": {}},
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "sota_trajectory_friction", "arguments": {"max_sessions": 12}},
            },
        ]
    )
    conv = resps[0]["result"]["structuredContent"]
    diag = resps[1]["result"]["structuredContent"]
    assert all(conv["harnesses"].values()), f"Missing sibling harness: {conv['harnesses']}"
    assert conv["peer_bus"]["online"] is True

    # Verify hcom, Claude/Codex global MCP registrations, and peer_hook_adapter.py
    assert (HOME / ".local" / "bin" / "hcom").is_file() or shutil.which("hcom"), "Missing aannoo/hcom CLI"
    req_mcps = {"sota-peer-bus", "agy-sota-core", "sota-mover-ranker"}
    c_servers = set((json.loads((HOME / ".claude.json").read_text(encoding="utf-8")).get("mcpServers") or {}).keys())
    assert req_mcps.issubset(c_servers), f"Claude missing MCPs: {sorted(req_mcps - c_servers)}"
    cx_txt = (HOME / ".codex" / "config.toml").read_text(encoding="utf-8", errors="ignore")
    for m in req_mcps:
        assert re.search(rf"^\[mcp_servers\.{re.escape(m)}\]", cx_txt, re.MULTILINE), f"Codex missing MCP {m}"

    adapter = AGENTS_ROOT / "bus" / "peer_hook_adapter.py"
    assert adapter.is_file(), f"Missing {adapter}"
    sys_py = "/usr/bin/python3" if Path("/usr/bin/python3").is_file() else sys.executable
    with tempfile.TemporaryDirectory() as tmpd:
        t_agents = Path(tmpd)
        t_bus = t_agents / "bus"
        t_bus.mkdir(parents=True)
        t_db = t_bus / "peer_bus.db"
        env_tmp = {**os.environ, "SOTA_AGENTS_ROOT": str(t_agents), "SOTA_PEER_BUS_DB": str(t_db)}
        sota_bus = str(AGENTS_ROOT / "bin" / "sota-bus")
        subprocess.run(
            [
                sota_bus,
                "claim",
                "--repo",
                "meridian",
                "--agent",
                "codex",
                "--session",
                "cx-99",
                "--paths",
                "*",
                "--intent",
                "editing",
            ],
            env=env_tmp,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        subprocess.run(
            [sota_bus, "msg", "--from", "agy-coord", "--to", "claude", "--repo", "agy-sota-harness", "sync check"],
            env=env_tmp,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )

        p_in = subprocess.run(
            [sys_py, str(adapter), "--agent", "claude", "--event", "UserPromptSubmit"],
            input=json.dumps({"session_id": "cc-1", "cwd": str(HARNESS_ROOT)}),
            capture_output=True,
            text=True,
            env=env_tmp,
            timeout=5,
            check=True,
        )
        assert "[SOTA Peer Message" in p_in.stdout

        p_deny = subprocess.run(
            [sys_py, str(adapter), "--agent", "codex", "--event", "PreToolUse"],
            input=json.dumps(
                {"tool_name": "Bash", "tool_input": {"command": "curl https://" + "api." + "alpaca.markets/v2/account"}}
            ),
            capture_output=True,
            text=True,
            env=env_tmp,
            timeout=5,
            check=True,
        )
        assert '"permissionDecision": "deny"' in p_deny.stdout

        p_ask = subprocess.run(
            [sys_py, str(adapter), "--agent", "claude", "--event", "PreToolUse"],
            input=json.dumps(
                {
                    "session_id": "cc-1",
                    "tool_name": "Edit",
                    "tool_input": {"file_path": str(DOCS / "meridian" / "AGENTS.md")},
                }
            ),
            capture_output=True,
            text=True,
            env=env_tmp,
            timeout=5,
            check=True,
        )
        assert '"permissionDecision": "ask"' in p_ask.stdout

    reg = json.loads((AGENTS_ROOT / "workflows" / "REGISTRY.json").read_text(encoding="utf-8"))
    wf_total = len(reg.get("workflows") or [])
    assert wf_total >= 9, f"Expected >=9 workflows in REGISTRY.json, found {wf_total}"

    cache_dir = HARNESS_ROOT / "cache"
    cache_dir.mkdir(exist_ok=True)
    (cache_dir / "session_brief.json").write_text(
        json.dumps({"convergence": conv, "trajectory_friction": diag}, indent=2) + "\n",
        encoding="utf-8",
    )
    return (
        f"3/3 harnesses + {len(conv['agy_plugins'])} AGY plugins + Claude/Codex 3/3 MCPs + "
        f"peer_hook_adapter + hcom + {wf_total}/{wf_total} workflows ({conv['mise_installed_families']} mise tool families)"
    )


PROBES: tuple[tuple[str, str, Callable[[], str]], ...] = (
    ("L0", "Provisioning, Lockfiles & 17-Repo Bridges", probe_l0),
    ("L1", "Lifecycle Hooks & Peer-Lease Collision Guard", probe_l1),
    ("L2", "Lean 7-Tool Core MCP & 4-Server Mesh", probe_l2),
    ("L3", "AST Symbol Graph & 18-Repo Shelf FTS5", probe_l3),
    ("L4", "16 Cross-Peer Skills, 8 Vendored Skills & 16 ADRs", probe_l4),
    ("L5", "Schema-Typed run_workflow Python DAGs", probe_l5),
    ("L6", "Anti-Slop Taste & Chrome DevTools", probe_l6),
    ("L7", "FTS5 Output Compression & Peer Bus CLIs", probe_l7),
    ("L8", "Deterministic ast-grep YAML Rule Pack", probe_l8),
    ("L9", "OS Seatbelt Policy, Gitleaks & Merge Gates", probe_l9),
    ("L10", "Scheduled Sidecars & Scoped Permissions", probe_l10),
    ("L11", "18/18 Trading Upstream Shelf Integrity", probe_l11),
    ("L12", "Multi-Peer Triad Convergence & SkillOpt", probe_l12),
)


def main() -> int:
    t0 = time.perf_counter()
    passed = 0
    print("# AGY Full-Landscape SOTA Harness Verification (`L0–L12` × `T0–T8` × `P0–P5`)")
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
