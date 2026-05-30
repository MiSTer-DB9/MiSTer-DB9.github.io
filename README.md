# MiSTer-DB9.github.io

Source for the MiSTer-DB9 website (served at <https://mister-db9.github.io/>).

Built with [MkDocs](https://www.mkdocs.org/) + the
[Material](https://squidfunk.github.io/mkdocs-material/) theme. The end-user guide
is **not duplicated here** — it lives in the public
[`Documentation`](https://github.com/MiSTer-DB9/Documentation) repo, pulled in as
a git submodule at `docs/vendor/`. The landing page and the generated
*Supported Cores* page are the only content owned by this repo.

Maintainer-facing docs are intentionally **not published** on this public site;
they live in the private
[`Documentation-Maintainer`](https://github.com/MiSTer-DB9/Documentation-Maintainer)
repo.

## Build locally

```bash
git submodule update --init          # fetch the Documentation content
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
mkdocs serve                         # live preview at http://127.0.0.1:8000
mkdocs build --strict                # static output -> site/ (fails on bad links)
```

## Refresh the Supported Cores page

`docs/cores.md` is generated from the canonical fork list in
[`Forks_MiSTer/Forks.ini`](https://github.com/MiSTer-DB9/Forks_MiSTer). Re-run it
when cores are added or removed (expects the `Forks_MiSTer` clone as a sibling
directory):

```bash
python tools/gen_cores.py ../Forks_MiSTer/Forks.ini
```

Saturn-port status is detected from sibling `<Core>_MiSTer/sys/joydb9saturn.v`
clones; when those aren't checked out the Saturn column is omitted.

## Update the docs content

The guides are edited in the `Documentation` repo. To pull the latest into the
site:

```bash
git submodule update --remote docs/vendor
git add docs/vendor && git commit -m "Bump Documentation submodule"
```

## Layout

| Path | Purpose |
|---|---|
| `mkdocs.yml` | Site config, theme, nav |
| `docs/index.md` + `overrides/home.html` | Custom landing page |
| `docs/stylesheets/extra.css` | Landing styling |
| `docs/cores.md` | Generated — see above |
| `docs/vendor/` | Submodule → `Documentation` repo |
| `tools/gen_cores.py` | Cores-page generator |

Licensed GPLv3, matching the rest of the MiSTer-DB9 fork.
