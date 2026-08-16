# Building

## Prerequisites

- **Python 3.11+** (3.13 tested)
- `pip install polib OpenCC` (the pipeline dependencies)
- **Poedit** (only for translating) — https://poedit.net/

mmarch comes from PATH: `npm i -g mmarch` (v5+).

Commands are run as `python -m mm678i18n <cmd>` from the repo root — the
docs write `mm678 <cmd>` for short. (`pip install -e .` optionally
installs `mm678` as a real command usable from anywhere.)

Note: the build itself is Windows-oriented (mmarch, case-insensitive
paths). `mm678 check` runs anywhere.

## One-click build

```
mm678 build                  # .po -> release zips, every language
mm678 build --langs zh_CN de # only these languages
mm678 apply zh_CN mmmerge D:\games\mmmerge   # copy the built package onto an install
mm678 build --no-release  # stop after postprod (skip the release zips)
```

Output lands in `build/` (git-ignored):
release zips in `build/release/out/`.

## Individual stages

```
mm678 templates    # regenerate build/templates_ctx after editing templates/
mm678 dev          # regenerate build/dev after source/template changes
mm678 mo           # compile .po -> .mo
mm678 prod         # translated game text -> build/prod
mm678 postprod     # installable trees -> build/postprod
mm678 release   # extract-over release .zip archives -> build/release/out
mm678 release --steps compose            # just assemble working dirs
mm678 check        # quality checks (po validity, encodings, line lengths)
mm678 zhconvert    # regenerate zh_TW .po from zh_CN via OpenCC
mm678 version      # show configured versions
```

## Day-to-day workflows

**Translation changed** (`.po` edited in Poedit): `mm678 build`.

**Game source text changed** (`source/` or `templates/` edited, e.g. a Merge
update — mind the CRLF/LF table format, see
[notes.md](notes.md#game-text-table-format-crlf-rows-lf-in-cell-line-breaks)): `mm678 templates && mm678 dev`, then open the `.po` in Poedit and
use *Translation → Update from source code* (it scans `build/dev`), translate
the new strings, then `mm678 build`.

**MM Merge update checklist** — see [release.md](release.md).

## Checks

`mm678 check` validates: every `.po` parses; every file in `source/` decodes
with its configured encoding; no over-long `.str` lines in `build/postprod`
(the engine crashes past 784 bytes/line). `mm678 check lf` additionally
reports bare-LF (soft line break) locations — informational only.
