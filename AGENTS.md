# Repository guide — for developers and AI agents

One-page orientation for anyone (human or AI) working in this repo. Deeper
docs: `docs/dev/architecture.md` (directory layout + pipeline),
`docs/dev/building.md` (commands + day-to-day workflows),
`docs/dev/new-language.md`, `docs/dev/release.md`, `docs/dev/notes.md`
(string-format constraints), `docs/dev/TODO.md` (known issues).

## What this is

Localization pipeline for Might and Magic 6/7/8 (GrayFace Patch) and MM Merge:
game text + gettext translations → per-language patch installers.

## Commands

```
pip install -e .                 # once; installs polib/OpenCC + the mm678 CLI
mm678 build                      # one-click: .po -> .mo -> game text -> postprod -> installers (.exe/.zip/.7z)
mm678 build --no-installers      # same, stop after postprod (no NSIS/7-Zip needed)
mm678 templates|dev|mo|prod|postprod|installers   # individual stages
mm678 check                      # po validity + source encodings + .str line lengths (CI runs po+encoding)
mm678 zhconvert                  # regenerate zh_TW .po from zh_CN (OpenCC)
mm678 new-language <lang>        # create a placeholder .po for a new language
```

`python -m mm678i18n …` works without installing. The build is Windows-oriented
(vendor/mmarch.exe, NSIS, case-insensitive paths); `mm678 check` runs anywhere.
There is no test suite — see "Verifying pipeline changes" below.

## Architecture (the parts that span multiple files)

Pipeline: `templates/`+`source/en` →(templates,dev)→ `build/dev/*.py` files
containing `_("...")`/`_x(ctx, "...")` calls; translators update
`translations/<lang>/LC_MESSAGES/mm678.po` from those via Poedit →(mo,prod)→
translated game text in each language's legacy encoding →(postprod)→
installable trees (DBCS re-encoding, fonts, Lua scripts, images, mmarch-packed
.lod archives) →(installers)→ NSIS .exe + portable .zip + .7z in
`build/setup/out/`. Core engine: `mm678i18n/pipeline.py`; asset assembly:
`mm678i18n/postprod.py`; packaging: `mm678i18n/setup_builder.py`.

- **Everything under `build/` is generated** — never hand-edit it; it is safe
  to delete. All tracked inputs live in `source/ templates/ translations/
  assets/ installer/ config/ vendor/`.
- **`config/languages.py` is the single source of truth** for per-language
  encoding, version, and DBCS font sizes. `config/versions.py` holds the
  installer matrix (`installers`) and release version; `config/settings.py`
  holds pipeline settings and all folder paths. Never duplicate language
  metadata elsewhere.
- **Language derivation**: languages with a folder in `source/` get .po
  generation; languages **built** (mo/prod/postprod) are `en` + the folders in
  `translations/`. Adding a language = adding its .po.
- **Shared files are stored once and distributed at build time**:
  `assets/scripts_datatables/_common/_all/` (every language × games in
  `settings.script_games`; `FNT_DBCS.lua` gets its per-language `fontSizes`
  line patched from `config/languages.py`), `_common/<game>/`,
  `assets/img/prod/<lang>/mmmerge_and_mm8/` (shipped to both games), and the
  `mm8_zh_update` installer = `zh` + `zh_update` additional trees. Do not
  re-introduce per-language/per-game copies of identical files.

## Invariants that are easy to break

- `translations/zh_TW/...mm678.po` is **generated** from zh_CN by
  `mm678 zhconvert` — don't edit it directly; add special-case words to the
  replace tables in `mm678i18n/zhconvert.py`.
- .po strings must never contain raw line breaks; soft line breaks are the
  two characters `\n` (see `lf_in_crlf_mode`). A bare newline in a msgstr
  breaks every gettext parser.
- `source/` and prod files use legacy game encodings (cp1252/gb2312/big5,
  declared in `config/languages.py`) — always honor the configured encoding
  when touching them.
- In the game's `.txt`/`.str` table files, **CRLF is the row separator and a
  bare LF is an in-cell line break** — any automatic LF↔CRLF conversion
  (editor save, git EOL conversion) corrupts them, hence the `-text`
  attributes in `.gitattributes`. Edit them only with an EOL-preserving
  editor or GrayFace's Txt Edit (`vendor/TxtEdit/`); see
  `docs/dev/notes.md`.
- Dev files are emitted as one `r.append(...)` statement per template line —
  do not "simplify" back to a single expression; a whole-file expression
  exceeds CPython's fixed compiler recursion limit (3.12+).
- Indentation is tabs (`.editorconfig`), including Python.
- `assets/sound/` and `assets/video/` are git-ignored local assets: CI-built
  installers lack the zh voice-over archives; full releases are built locally.
- If `mm678 installers` prints a "FILE COPYING block differs" warning, the
  file list changed and a human must review the corresponding
  `installer/nsi/<lang>/<target>/mm_i18n.nsi` — this is the one remaining
  manual review point in the pipeline.

## Verifying pipeline changes

When changing pipeline code, prove output equivalence rather than eyeballing:
run the affected stages before and after and byte-compare the `build/` trees
(hash every file; ignore `__pycache__`/`nonprod`). For comparisons against
older revisions, build a baseline in a throwaway `git worktree`. `.lod`
archives produced by mmarch are deterministic, so they compare byte-for-byte
too.
