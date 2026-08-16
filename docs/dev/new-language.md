# Adding a new language

Example: French (`fr`).

## 1. Declare the language

`config/languages.py` — make sure the language has an entry with the right
game encoding (already present for the common European/CJK languages):

```python
'fr': {'encoding': 'cp1252', 'i18n_version': '2.3'},
```

For a DBCS (CJK) language also set `dbcs_fonts` (the BDF font per engine
font — see `docs/dev/fonts.md`; entries for zh/ja/ko already exist).

## 2. Create the .po

```
mm678 new-language fr
```

This writes `translations/fr/LC_MESSAGES/mm678.po` with every translatable
string and empty translations (a placeholder — building it produces an
English-text patch for that language).

If you have existing translated game files (e.g. from an official French
release), put them under `source/fr/` mirroring the game folder layout, set
`source_encoding` for the language in `config/languages.py` if the files are
not UTF-8, and run:

```
mm678 new-language fr --seed-from-source
```

to harvest translations from them (conflicts are resolved by the
`conflict_priority` rules in `config/settings.py`; add `custom_list` entries
there for manual overrides).

## 3. Translate

Open the `.po` in Poedit and translate. For a Traditional↔Simplified Chinese
pair, `mm678 zhconvert` converts automatically via OpenCC.

## 4. Build

```
mm678 build --no-installers
```

`build/postprod/fr/` now holds the installable file trees. To also produce
installers, add the language's targets to `installers` in
`config/versions.py` (plus an `installer/nsi/fr/<target>/mm_i18n.nsi`,
copied and adapted from an existing one) and run `mm678 installers`.

## Notes

- The reference text is `source/en` + `templates/`; never edit generated
  files under `build/`.
- Translatable-string rules (placeholders like `%lu`, `%30`…) are documented
  in [notes.md](notes.md).
