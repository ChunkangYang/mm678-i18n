# Adding a new language

Example: French (`fr`).

## 1. Declare the language

`config/languages.toml` — make sure the language has an entry with the right
game encoding (already present for the common European/CJK languages):

```toml
[languages.fr]
encoding = "cp1252"
i18n_version = "2026-08-16"
```

For a DBCS (CJK) language also set `dbcs_fonts` (the three BDF files —
see `docs/dev/fonts.md`; entries for zh/ja/ko already exist).

## 2. Create the .po

```
mm678 new-language fr
```

This writes `translations/fr/mm678.po` with every translatable
string and empty translations (a placeholder — building it produces an
English-text patch for that language).

If you have existing translated game files (e.g. from an official French
release) and want to pre-seed the `.po` from them, write a one-off harvest
script with `polib` (match strings per file/row against `source/en`, in the
spirit of `tools/recover_po.py`). The old `--seed-from-source` bootstrap
path was removed — it assumed line-for-line parity with the English files,
which official localizations don't guarantee.

## 3. Translate

Open the `.po` in Poedit and translate. Start with the terminology: translate
the strings listed in `references/glossary/glossary-terms.tsv` first, run
`python tools/build_glossary.py fr` to produce
`references/glossary/fr/glossary.jsonl`, then translate everything else
following that table (see the "Translation glossary" section in `AGENTS.md`).
For a Traditional↔Simplified Chinese pair, `mm678 zhconvert` converts
automatically via OpenCC.

## 4. Build

```
mm678 build --no-release
```

`build/postprod/fr/` now holds the installable file trees. To also produce
release zips, add the language's targets to `releases` in
`config/versions.toml` and run `mm678 release`.

## Notes

- The reference text is `source/en` + `templates/`; never edit generated
  files under `build/`.
- Translatable-string rules (placeholders like `%lu`, `%30`…) are documented
  in [notes.md](notes.md).
