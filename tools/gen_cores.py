#!/usr/bin/env python3
"""Generate docs/cores.md (the Supported Cores page) from Forks_MiSTer/Forks.ini.

The site is built standalone from the committed docs/cores.md; this script
refreshes that file from the canonical fork list. Run it after Forks.ini changes:

    python tools/gen_cores.py ../Forks_MiSTer/Forks.ini

Saturn-port status is detected the same way the project does it (AGENTS.md truth
source): a core counts as Saturn-ported iff <core_dir>/sys/joydb9saturn.v exists.
Core dirs are looked up as siblings of the repo (../<RELEASE_CORE_NAME>_MiSTer).
When the sibling clone is absent the Saturn column is left blank rather than wrong.
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


def is_saturn_ported(repo_root: str, core_name: str) -> bool | None:
    core_dir = os.path.join(repo_root, "..", f"{core_name}_MiSTer")
    if not os.path.isdir(core_dir):
        return None  # sibling clone absent -> unknown
    return os.path.isfile(os.path.join(core_dir, "sys", "joydb9saturn.v"))


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path/to/Forks.ini>", file=sys.stderr)
        return 2
    forks_ini = sys.argv[1]
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    syncing, sections = read_forks(forks_ini)

    rows: list[tuple[str, str, str, str]] = []
    saturn_known = False
    for sec in syncing:
        if sec in SKIP_SECTIONS:
            continue
        meta = sections.get(sec, {})
        name = meta.get("RELEASE_CORE_NAME", sec.removesuffix("_DB9"))
        fork = meta.get("FORK_REPO", "")
        upstream = meta.get("UPSTREAM_REPO", "")
        fork_cell = f"[{repo_slug(fork)}]({fork[:-4] if fork.endswith('.git') else fork})" if fork else "—"
        up_cell = f"[upstream]({upstream[:-4] if upstream.endswith('.git') else upstream})" if upstream else "—"
        sat = is_saturn_ported(repo_root, name)
        if sat is not None:
            saturn_known = True
        sat_cell = "✅" if sat else ("" if sat is None else "")
        rows.append((name, fork_cell, up_cell, sat_cell))

    rows.sort(key=lambda r: r[0].lower())

    out = [
        "<!-- GENERATED FILE — do not edit by hand.",
        "     Refresh with: python tools/gen_cores.py ../Forks_MiSTer/Forks.ini -->",
        "",
        "# Supported Cores",
        "",
        f"MiSTer-DB9 ships DB9 / DB15 / SNAC8 controller support across "
        f"**{len(rows)} cores**, each kept in sync with its MiSTer-devel upstream "
        "by automated CI/CD. Every core below has its own fork repo; the build is "
        "distributed through the [ENCC distribution database]"
        "(https://github.com/MiSTer-DB9/Distribution_MiSTer).",
        "",
    ]
    if saturn_known:
        out.append(
            "The **Saturn** column marks cores with key-gated Saturn adapter support "
            "(`sys/joydb9saturn.v`), unlocked by `db9pro.key`. A blank cell means "
            "DB9MD / DB15 / SNAC8 only."
        )
        out.append("")
        out.append("| Core | Fork repo | Upstream | Saturn |")
        out.append("|---|---|---|:---:|")
        for name, fork, up, sat in rows:
            out.append(f"| {name} | {fork} | {up} | {sat} |")
    else:
        out.append("| Core | Fork repo | Upstream |")
        out.append("|---|---|---|")
        for name, fork, up, _sat in rows:
            out.append(f"| {name} | {fork} | {up} |")
    out.append("")

    dest = os.path.join(repo_root, "docs", "cores.md")
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print(f"wrote {dest} ({len(rows)} cores, saturn_known={saturn_known})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
