# Translation & i18n technical notes

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
