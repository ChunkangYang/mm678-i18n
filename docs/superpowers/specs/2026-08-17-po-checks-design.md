# Unified .po content checks — design

**Date:** 2026-08-17
**Status:** approved, ready for implementation planning

## Problem

`mm678 check po` only verifies that each `.po` file parses. Nothing inspects
entry content, so two classes of defect ship undetected:

1. **Placeholder corruption** — a translation drops, duplicates, or reorders
   the substitution tokens the game engine fills in.
2. **Whitespace and line-break drift** — a translation gains leading/trailing
   spaces, tabs, or line breaks the source does not have. `trim_whitespace` is
   `false` in `config/settings.toml`, so this reaches the game verbatim.

A survey of all 13 `.po` files (2026-08-17) found **228 real placeholder
defects** already in the repository.

## Survey findings

These numbers drive the design; re-derive them before trusting them again.

### Placeholder families

Two disjoint families are in use, and they need different rules:

| Family | Forms | Count in msgid (zh_CN) | Engine behaviour |
|---|---|---|---|
| printf | `%s` `%d` `%u` `%lu` | 105 / 33 / 17 / 26 | filled **positionally** — order is load-bearing |
| MM numbered token | `%01`–`%34` | 700+ | each number is self-identifying — order is free |

Literal `%` in prose is common (`100% behind`, `2.064%`, `10% chance per
point of`). A general printf grammar mis-reads these as `% b`, `% c`, `% p`,
`%-p`. The checks therefore match an **allowlist of the forms this project
actually uses**, never a general grammar.

### Existing violations

| Aspect | Count | Verdict |
|---|---|---|
| placeholder multiset differs | 220 (1–39 per language) | real defects |
| printf order differs | 8 (ja 6, it 1, pl 1) | real defects |
| numbered-token order differs | 31 (zh_CN 26) | legitimate word order |
| bare TAB in msgstr | 0 | free to enforce |
| CR in msgstr | 0 | free to enforce |
| literal `\n` two-char in msgstr | 0 | free to enforce |
| LF count differs | ~2100 per language (~24 000 total) | mostly legitimate |
| trailing whitespace differs | 126–1667 per language | mostly legitimate |

Example of a genuine printf defect:

```
[it] msgid  'It will take %d day to cross to %s.'
     msgstr 'La traversata fino a %s durerà %d giorno/i.'
```

The engine feeds the day count into `%s` and the destination string into
`%d` — garbage output or a crash.

### Direction of the whitespace/newline differences

The bulk of the ~24 000 differences run one way, and that way is correct:

| Direction | zh_CN count | Verdict |
|---|---|---|
| msgid has LF, msgstr does not (translator merged lines) | 1935 (84%) | legitimate — CJK does not need English line breaks |
| msgstr adds LF the msgid lacks | 200 | worth reporting |
| both have LF, counts differ | 174 | worth reporting |
| msgid has trailing spaces, msgstr dropped them | the large majority | legitimate — source padding |
| **msgstr adds trailing whitespace** | **6** | suspicious, ships into the game |
| msgid has leading whitespace, msgstr dropped it | most | legitimate |
| **msgstr adds leading whitespace** | **0** | — |

Counts in the two rows marked suspicious compare runs of `' '` only. An
earlier pass used bare `strip()`, which also consumes `\n` and `\t` and so
reported 14 and 7; the space-only rule is the one the checks implement.

zh_CN is the best-behaved language here. Repo-wide the directional rule
reports **8110** differences (5544 whitespace, 2566 newline), spread very
unevenly: ko contributes 1426 added trailing spaces and ru 1036, against
zh_CN's 6. Because `trim_whitespace = false`, every one of those reaches the
game verbatim.

Examples of the suspicious direction:

```
msgid  "Abdul's Discount Magic Supplies"
msgstr '阿卜杜的廉价魔法器具 '        # one trailing space

msgid  'Message from Mr. Stantley'
msgstr '斯坦利先生的来信   '          # three trailing spaces
```

## Design

### Module layout

`checks.py` is 141 lines and mixes concerns already. Entry-level `.po`
checking goes in its own module.

```
mm678i18n/pocheck.py       new — entry-level .po checks + allowlist
mm678i18n/checks.py        keeps encoding / source-LF / line-length;
                           delegates its 'po' entry to pocheck
config/po_allowlist.toml   new — entry-level exemptions
tests/test_pocheck.py      new — unit tests over inline .po fixtures
```

`pocheck.py` exposes one function:

```python
def run(langs = None, strict = False, showExempt = False, printKey = None) -> int
```

It returns the number of FAIL-level problems. `checks.py` does not need to
know how many sub-checks exist inside it.

### Check inventory

All of these run under the single command `mm678 check po`.

| Sub-check | Rule | Level |
|---|---|---|
| `parse` | polib parses the file | FAIL |
| `placeholder-set` | the **combined multiset** of printf tokens and numbered tokens matches between msgid and msgstr (one comparison over both families, so a `%s` swapped for a `%01` is caught) | FAIL |
| `placeholder-order` | **printf family only** — the printf subsequence of msgstr equals that of msgid, ignoring any numbered tokens between them | FAIL |
| `tab` | msgstr contains no bare TAB (TAB is the field separator) | FAIL |
| `cr` | msgstr contains no CR | FAIL |
| `literal-slash-n` | msgstr contains no literal two-char `\n` (prod's `slashN2Lf` would turn it into a real break) | FAIL |
| `whitespace` | msgstr adds no leading/trailing whitespace beyond the msgid's | WARN |
| `newline` | msgstr adds no LF beyond the msgid's | WARN |

Numbered tokens are deliberately exempt from `placeholder-order`.

Placeholder patterns:

```python
PRINTF = r'%(?:lu|[sdu])'    # the four forms the project actually uses
NUMTOK = r'%[0-9]{1,2}'      # MM's %01–%34
```

Entries that are obsolete, untranslated (`msgstr == ''`), or fuzzy are
skipped by every content check.

### Severity and exit codes

- FAIL counts toward the problem total; `mm678 check` exits 1; CI blocks.
- WARN prints but does not affect the exit code. Whitespace and newline
  differences are reported, never required to match the source.
- `--strict` promotes WARN to FAIL.

### Allowlist — two layers

**Layer 1: built-in directional rule.** No maintenance.

> A translation with *less* whitespace or *fewer* line breaks than the source
> is silently exempt. Only *additions* are reported.

Rationale: source trailing spaces are table padding and source line breaks
are English typesetting; removing them is correct. Additions reach the game
verbatim because `trim_whitespace = false`.

For zh_CN this exempts 2523 differences and reports 213 (6 trailing-space
additions, 207 added line breaks). `--show-exempt` lists what the rule
suppressed.

**Layer 2: per-entry allowlist**, `config/po_allowlist.toml`.

```toml
[[allow]]
key    = "3f9a1c04be77"
lang   = "zh_CN"
checks = ["newline"]
msgid  = "Etched into the tree a…"
reason = "source pads with trailing spaces; the Chinese uses an explicit break"
```

`key` is `sha1(msgctxt + "\x04" + msgid).hexdigest()[:12]`. `msgctxt` alone
is not unique — it holds semantic tags like `location` and `npcprof`, shared
across thousands of entries — so the gettext identity pair is the key.
Hashing keeps the key stable when the `.po` is re-sorted or renumbered.

`checks` scopes the exemption to named sub-checks; everything else still
applies to that entry. `msgid` and `reason` are documentation; the code reads
only `key`, `lang`, and `checks`.

`mm678 check po --print-key <lang>` emits ready-to-paste keys for the
entries currently being reported.

### Output

Extends the existing `OK` / `FAIL` / `SKIP` prefixes with `WARN`:

```
== check: po ==
OK   translations/de/mm678.po  (17668 entries, 100% translated)
FAIL translations/ja/mm678.po:8821  placeholder-order
       msgid  'Become %s in %s for %lu gold'      -> [%s, %s, %lu]
       msgstr '%luゴールドを払い、%sの%sになる'     -> [%lu, %s, %s]
       printf placeholders are filled positionally; reordering mismatches types
WARN translations/zh_CN/mm678.po:2043  whitespace
       msgstr has 1 extra trailing space: '阿卜杜的廉价魔法器具 '
228 problem(s), 8110 warning(s).
```

### CLI

**No new top-level subcommand.** Every `.po` check lives under the existing
`po` name, so "unify the po checks into one command" means `mm678 check po`
runs all eight of them — not `check placeholder`, `check whitespace`, and so
on as sibling names. The check names (`po`, `encoding`, `lf`, `linelength`)
and the default set are unchanged, so bare `mm678 check` and the CI
invocation keep working; the `po` entry simply starts inspecting content.

```
mm678 check                          # default set: po + encoding + linelength
mm678 check po                       # all eight po checks
mm678 check po --strict              # promote WARN (whitespace, newline) to FAIL
mm678 check po --show-exempt         # also list what the directional rule suppressed
mm678 check po --print-key zh_CN     # emit paste-ready allowlist keys
mm678 check po --langs ja it pl      # restrict to named languages
```

The four flags affect only the `po` check. `--langs` matches the spelling
used by `mo`, `prod`, `postprod`, `release`, and `build`.

### Testing

The repository has no test suite yet. `tests/test_pocheck.py` builds small
`.po` fixtures as inline strings — no dependency on the real translations, so
the tests stay valid as translations change. Coverage:

- one pass case and one fail case per sub-check
- the directional rule exempts removals and reports additions
- an allowlist entry suppresses only its named sub-check
- literal `%` in prose (`100% chance`) produces no placeholder finding
- numbered-token reordering produces no finding; printf reordering does
- obsolete, fuzzy, and untranslated entries are skipped

### Documentation

- `docs/dev/building.md` — the check-list paragraph (lines ~42, ~61)
- `AGENTS.md` — line 29
- `CONTRIBUTING.md` — line 12
- `docs/dev/notes.md` — why printf order is enforced and numbered-token
  order is not; how the two allowlist layers interact

## Consequence to plan for

Once merged, `mm678 check` reports **228 FAIL** immediately (220 multiset,
8 order) and CI goes red. These are genuine defects, but fixing them is
separate work. Land the checks first, then do one focused pass over the
placeholder defects.

## Explicitly out of scope

- Fixing the 228 existing placeholder defects
- Any change to `trim_whitespace`, `lf_in_crlf_mode`, or the build pipeline
- Checks on `.pot` files or on source `.txt`/`.str` tables
- Plural-form validation (`pluralforms.py` already owns that area)
