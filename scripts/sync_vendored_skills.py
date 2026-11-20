#!/usr/bin/env python3
"""Sync or verify pinned MIT upstream skills declared in `.agents/skills/UPSTREAM_SKILL_PINS.json`."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS_FILE = ROOT / ".agents" / "skills" / "UPSTREAM_SKILL_PINS.json"
SIBLING_CACHE = next(
    (
        cand
        for cand in (
            Path("C:/sota-workstation/cc-sota-harness/.agents/skills"),
            Path.home() / "sota-workstation" / "cc-sota-harness" / ".agents" / "skills",
            Path.home() / "Documents" / "cc-sota-harness" / ".agents" / "skills",
        )
        if cand.is_dir()
    ),
    Path.home() / "Documents" / "cc-sota-harness" / ".agents" / "skills",
)


def main() -> int:
    pins = json.loads(PINS_FILE.read_text(encoding="utf-8"))
    dest_root = ROOT / ".agents" / "skills"
    synced = 0
    for src_entry in pins.get("sources") or []:
        for sname in src_entry.get("skills") or []:
            target = dest_root / sname
            if (target / "SKILL.md").is_file():
                synced += 1
                continue
            donor = SIBLING_CACHE / sname
            if (donor / "SKILL.md").is_file():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(donor, target)
                synced += 1
            else:
                print(f"[WARN] Missing local donor for pinned skill '{sname}'", file=sys.stderr)
                return 1
    # Ensure every canonical skill in ~/.agents/skills/ is symlinked across AGY, Claude Code, and Codex
    agents_skills = Path.home() / ".agents" / "skills"
    peer_roots = (
        Path.home() / ".gemini" / "config" / "skills",
        Path.home() / ".claude" / "skills",
        Path.home() / ".codex" / "skills",
    )
    peer_synced = 0
    if agents_skills.is_dir():
        for sdir in sorted(agents_skills.iterdir()):
            if not (sdir / "SKILL.md").is_file():
                continue
            for proot in peer_roots:
                proot.mkdir(parents=True, exist_ok=True)
                link = proot / sdir.name
                if not link.exists() and not link.is_symlink():
                    try:
                        link.symlink_to(sdir)
                    except OSError:
                        shutil.copytree(sdir, link, dirs_exist_ok=True)
                    peer_synced += 1

    print(
        f"[SKILL-SYNC OK] Verified {synced} pinned upstream skills + converged ~/.agents/skills ({peer_synced} new links)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
