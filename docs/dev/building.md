# Building

## Prerequisites

- **Python 3.9+** (3.13 tested)
- `pip install -e .` in the repo root (installs `polib`, `OpenCC` and the
  `mm678` command)
- **NSIS** (only for `installers`) — https://nsis.sourceforge.io/ or
  `winget install NSIS.NSIS`. Auto-detected; override with the `MAKENSIS`
  environment variable.
- **7-Zip** (only for `installers`) — https://www.7-zip.org/. Auto-detected;
  override with the `SEVENZIP` environment variable.
- **Poedit** (only for translating) — https://poedit.net/

`vendor/mmarch.exe` ships in the repo; no setup needed.

Note: the build itself is Windows-oriented (mmarch, NSIS, case-insensitive
paths). `mm678 check` runs anywhere.

## One-click build

```
mm678 build                  # .po -> installers, everything
mm678 build --no-installers  # stop after postprod (no NSIS/7-Zip needed)
```

Output lands in `build/` (git-ignored):
installers in `build/setup/out/`.

## Individual stages

```
mm678 templates    # regenerate build/templates_ctx after editing templates/
mm678 dev          # regenerate build/dev after source/template changes
mm678 mo           # compile .po -> .mo
mm678 prod         # translated game text -> build/prod
mm678 postprod     # installable trees -> build/postprod
mm678 installers   # NSIS .exe + portable .zip + .7z -> build/setup/out
mm678 installers --steps compose            # just assemble working dirs
mm678 check        # quality checks (po validity, encodings, line lengths)
mm678 zhconvert    # regenerate zh_TW .po from zh_CN via OpenCC
mm678 version      # show configured versions
```

## Day-to-day workflows

**Translation changed** (`.po` edited in Poedit): `mm678 build`.

**Game source text changed** (`source/` or `templates/` edited, e.g. a Merge
update): `mm678 templates && mm678 dev`, then open the `.po` in Poedit and
use *Translation → Update from source code* (it scans `build/dev`), translate
the new strings, then `mm678 build`.

**MM Merge update checklist** — see [release.md](release.md).

## Checks

`mm678 check` validates: every `.po` parses; every file in `source/` decodes
with its configured encoding; no over-long `.str` lines in `build/postprod`
(the engine crashes past 784 bytes/line). `mm678 check lf` additionally
reports bare-LF (soft line break) locations — informational only.
