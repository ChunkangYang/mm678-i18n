# Contributing

Thanks for helping localize Might and Magic 6/7/8 and MM Merge!

## Improve an existing translation

1. Fork and clone the repo.
2. Edit `translations/<lang>/LC_MESSAGES/mm678.po` — with
   [Poedit](https://poedit.net/) (recommended) or any editor that produces
   valid gettext syntax. Do not put raw line breaks inside a `msgstr`; use
   `\n`.
3. Run `mm678 check po` (see [docs/dev/building.md](docs/dev/building.md)
   for setup) to make sure the file still parses.
4. Open a pull request. CI validates the `.po` files and encodings.

To test in-game: `mm678 build --no-installers` and copy
`build/postprod/<lang>/<game>/` over your game folder (back it up first).

## Add a new language

See [docs/dev/new-language.md](docs/dev/new-language.md) — start with
`mm678 new-language <lang>`.

## Editing game text tables directly

The `.txt`/`.str` files under `source/` and `templates/` are CRLF/LF-sensitive
tables (CRLF separates rows; a bare LF is an in-cell line break). Editors or
git settings that normalize line endings will corrupt them — read the format
rules in [docs/dev/notes.md](docs/dev/notes.md) first, and prefer GrayFace's
[Txt Edit](https://grayface.github.io/mm/#Txt-Edit) (in `vendor/TxtEdit/`).

## Report problems

Open a GitHub issue. For wrong/missing translations, include a screenshot
and where in the game you saw it. Known issues are tracked in
[docs/dev/TODO.md](docs/dev/TODO.md).

## Code

The pipeline lives in `mm678i18n/` (config in `config/`). Match the existing
style (tabs, camelCase helpers). `mm678 check` must pass; if you change the
pipeline, verify `mm678 build --no-installers` still succeeds before and
after, and that the output under `build/` is unchanged unless the change is
intentional.

## 中文贡献者

直接用 Poedit 编辑 `translations/zh_CN/LC_MESSAGES/mm678.po`（简体）；繁体由
`mm678 zhconvert` 从简体自动转换生成，请不要单独修改繁体 `.po`（个别需要
繁体特殊处理的词请在 `mm678i18n/zhconvert.py` 的替换表中添加）。
