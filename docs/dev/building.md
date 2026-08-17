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
release zips in `build/release/out/`. `build/cache/` holds the
packed-archive cache (content-keyed; unchanged folders reuse the cached
.lod/.snd instead of re-packing — delete it to force a full re-pack).

## Individual stages

```
mm678 templates    # regenerate build/templates_ctx after editing templates/
mm678 dev          # regenerate build/dev after source/template changes
mm678 mo           # compile .po -> .mo
mm678 prod         # translated game text -> build/prod
mm678 postprod     # installable trees -> build/postprod (parallel per language; --jobs 1 = serial)
mm678 release   # extract-over release .zip archives -> build/release/out
mm678 release --steps compose            # just assemble working dirs
mm678 check        # quality checks (po content, encodings, line lengths)
mm678 check po --strict            # treat whitespace/newline warnings as failures
mm678 check po --print-key <lang>  # allowlist keys for the reported entries
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

`mm678 check` validates: every `.po` parses and its entries survive the
content checks below; every file in `source/` decodes with its configured
encoding; no over-long `.str` lines in `build/postprod` (the engine crashes
past 784 bytes/line). `mm678 check lf` additionally reports bare-LF (soft
line break) locations — informational only.

`mm678 check po` runs eight checks over every entry. Obsolete, fuzzy, and
untranslated entries are skipped.

| Check | Rule | Level |
|---|---|---|
| `parse` | the file is valid gettext | FAIL |
| `placeholder-set` | msgid and msgstr hold the same multiset of placeholders | FAIL |
| `placeholder-order` | printf placeholders (`%s` `%d` `%u` `%lu`) appear in the same order | FAIL |
| `tab` | msgstr has no bare TAB (TAB is the table field separator) | FAIL |
| `cr` | msgstr has no CR | FAIL |
| `literal-slash-n` | msgstr has no literal backslash-n | FAIL |
| `whitespace` | msgstr adds no leading/trailing spaces | WARN |
| `newline` | msgstr adds no line breaks | WARN |

FAIL sets a non-zero exit code; WARN does not. `--strict` promotes warnings.

MM's numbered tokens (`%01`–`%34`) are deliberately exempt from
`placeholder-order` — each number identifies itself, so reordering them is
normal translation work. See [notes.md](notes.md#percent-sign-placeholders).

**Allowlist.** Two layers suppress legitimate differences. The built-in
directional rule exempts any translation with *less* whitespace or *fewer*
line breaks than the source: source trailing spaces are table padding and
source breaks are English typesetting, so dropping them is correct. For a
difference that survives that rule and is still correct, add an entry to
`config/po_allowlist.toml`; `mm678 check po --print-key <lang>` prints
paste-ready keys, and `--show-exempt` lists what the directional rule hid.
