#!/usr/bin/env python3
"""Generate docs/cores.md (the Supported Cores page) from Forks_MiSTer/Forks.ini.

The site is built standalone from the committed docs/cores.md; this script
refreshes that file from the canonical fork list. Run it after Forks.ini changes:

    python tools/gen_cores.py ../Forks_MiSTer/Forks.ini

Saturn adapter support is now universal across every fork (each core ships
sys/joydb9saturn.v), so the page no longer carries a per-core Saturn column —
just a note in the preamble.
"""

from __future__ import annotations

import os
import re
import sys

# Infra-only fork sections that are not user-facing FPGA cores.
SKIP_SECTIONS = {"Main_DB9", "menu_DB9", "InputTest_DB9"}


def read_forks(path: str) -> tuple[list[str], dict[str, dict[str, str]]]:
    """Parse Forks.ini by hand (configparser would choke on the bare list value
    and strip the inline-comment semantics the repo's own tooling preserves)."""
    syncing: list[str] = []
    sections: dict[str, dict[str, str]] = {}
    current: str | None = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            m = re.match(r"^\[(.+?)\]\s*$", line)
            if m:
                current = m.group(1)
                sections.setdefault(current, {})
                continue
            if current == "Forks" and line.strip().startswith("SYNCING_FORKS"):
                _, _, val = line.partition("=")
                syncing = val.split()
                continue
            if current and "=" in line and not line.lstrip().startswith("#"):
                key, _, val = line.partition("=")
                sections[current][key.strip()] = val.strip()
    return syncing, sections


def repo_slug(url: str) -> str:
    """https://github.com/MiSTer-DB9/Foo_MiSTer.git -> MiSTer-DB9/Foo_MiSTer"""
    s = url.strip()
    s = re.sub(r"^https?://github\.com/", "", s)
    s = re.sub(r"\.git$", "", s)
    return s


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path/to/Forks.ini>", file=sys.stderr)
        return 2
    forks_ini = sys.argv[1]
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    syncing, sections = read_forks(forks_ini)

    rows: list[tuple[str, str, str]] = []
    for sec in syncing:
        if sec in SKIP_SECTIONS:
            continue
        meta = sections.get(sec, {})
        name = meta.get("RELEASE_CORE_NAME", sec.removesuffix("_DB9"))
        fork = meta.get("FORK_REPO", "")
        upstream = meta.get("UPSTREAM_REPO", "")
        fork_cell = f"[{repo_slug(fork)}]({fork[:-4] if fork.endswith('.git') else fork})" if fork else "—"
        up_cell = f"[upstream]({upstream[:-4] if upstream.endswith('.git') else upstream})" if upstream else "—"
        rows.append((name, fork_cell, up_cell))

    rows.sort(key=lambda r: r[0].lower())

    out = [
        "<!-- GENERATED FILE — do not edit by hand.",
        "     Refresh with: python tools/gen_cores.py ../Forks_MiSTer/Forks.ini -->",
        "",
        "# Supported Cores",
        "",
        f"MiSTer-DB9 ships DB9 / DB15 / Saturn controller support across "
        f"**{len(rows)} cores**, each kept in sync with its MiSTer-devel upstream "
        "by automated CI/CD. Every core below has its own fork repo; the build is "
        "distributed through the [ENCC distribution database]"
        "(https://github.com/MiSTer-DB9/Distribution_MiSTer).",
        "",
        "Every core supports the DB9MD and DB15 `UserIO Joystick` adapters, plus "
        "the key-gated **Saturn** adapter (`sys/joydb9saturn.v`), unlocked at "
        "runtime by `db9pro.key`.",
        "",
        "| Core | Fork repo | Upstream |",
        "|---|---|---|",
    ]
    for name, fork, up in rows:
        out.append(f"| {name} | {fork} | {up} |")
    out.append("")

    dest = os.path.join(repo_root, "docs", "cores.md")
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print(f"wrote {dest} ({len(rows)} cores)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
