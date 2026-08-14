# Translation & i18n technical notes

## Game text table format: CRLF rows, LF in-cell line breaks

The game's `.txt`/`.str` table files (as extracted from `.lod` archives —
i.e. everything under `source/`, `templates/` and the generated prod trees)
are tab-separated tables in which the **row separator is CRLF** (`
`),
while a **bare LF** (`
`) inside a cell is a soft line break that makes the
cell's text multi-line.

Consequences:

- Any automatic newline conversion — a text editor normalizing line endings
  on save, or git's CRLF/LF conversion — silently corrupts these files by
  merging rows or splitting cells. This is why `.gitattributes` marks
  `*.txt` and `*.str` as `-text` (stored and checked out verbatim, no EOL
  conversion). Never remove those attributes.
- If you edit these files directly, use an editor that preserves line
  endings exactly, or better use GrayFace's
  [Txt Edit](https://grayface.github.io/mm/#Txt-Edit), a table editor made
  for this format — it ships in this repo at `vendor/TxtEdit/`.
- The pipeline itself is EOL-exact: files are read/written with explicit
  newline handling, and an in-cell LF is represented inside `.po` files as
  the two characters `
` (`lf_in_crlf_mode` in `config/settings.py`),
  converted back to a real LF when the prod files are generated.
- `mm678 check lf` lists all in-cell LF locations in the source tables
  (informational — they are legitimate).

## String format constraints (i18n readiness)

- The localized string for `You found %lu gold (followers take %lu)!` must
  always end with `%lu)!`.
- In the localized string for `You win!  +3 Skill Points` (+3 can be +5, +7
  or +10), `+` must always be preceded by two spaces.
- `.str` lines must stay under 784 bytes in the game encoding
  (`mm678 check linelength` enforces this).
- Do not put raw line breaks in a `msgstr`; embedded soft line breaks are
  written as `\n` (see `lf_in_crlf_mode` in `config/settings.py`).

## Percent-sign placeholders

- MM8 & MM Merge history articles:
  - `%30`: date of the history article (e.g. “February 4, 1172”)
  - `%31`: main character's name
  - `%32`: his/her (possessive) — `%33`: he/she — `%34`: him/her
- MM7 history: `%30` date; `%31`–`%34`: the four characters' names.
- MM6 NPCbtb:
  - `%01` NPC名字 · `%02` 角色名字 · `%03`/`%09` NPC第三人称所有格
  - `%04` 贿赂金币数量 · `%05` 时间（“早晨”等） · `%06` 先生/女士
  - `%07` 爵士Sir/夫人Lady · `%08` Award（完成的任务）之一
  - `%10` 爵士Lord/夫人Lady · `%11`/`%12` 声誉 · `%13` 随机名字
  - `%14`/`%16` 兄弟/姐妹（按NPC性别） · `%15` 女儿（角色是男的也如此，原版bug）

## Localization plumbing

- `Data/LocalizeTables.ZHCN_NPCNames.txt` works with
  `Scripts/General/NPCNewsTopics.lua`'s `ProcessNamesTXT()`.
- News topics (last lines of `area.txt`) work with `ProcessMapNewsTXT()`.
- The mmmerge icons archive is named `z10 Loc<LANG>.icons.lod` (the `z`
  prefix is required for load order).

## File usefulness survey (MM6 .STR etc.)

Not needed: `DDB1.STR`, `intro.STR`, `INTRO.TXT`, `Lose.STR`,
`LWSPIRAL.STR`, `NPCDATA.STR`, `SPIRAL.STR`, `Win.STR`, `NWC.STR`,
`NPCGroup.txt`, `T1.STR`–`T8.STR`, `7Out09.STR`–`7Out12.STR`, `7Out14.STR`,
`ZDDB02.STR`–`ZDDB10.STR`, `ZDTL01.STR`, `ZDTL02.STR`, `ZDWJ*.STR`.

Useful: `roster.txt`.

## LocalizeTables conflict example

The Merge "Path of Light/Dark" strings (2102–2109) overwrite the barrel
strings (2102–2109) — first table wins:

```
2102 Path of Light            vs  2102 The barrel is empty
2103 Path of Dark             vs  2103 +1 Might permanent
...
```
