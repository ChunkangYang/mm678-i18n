# Architecture

The project turns the games' original text files plus gettext translations
into per-language patch installers.

## Repository layout

| Path | Tracked | What it is |
|---|---|---|
| `source/` | ✔ | Original game text files per language (`en/` is the reference; other folders hold pre-existing translated game files used only to seed a language) |
| `templates/` | ✔ | Game text files with every translatable cell replaced by `_(TRANS)_` |
| `translations/` | ✔ | gettext files: `mm678.pot` + `<lang>/LC_MESSAGES/mm678.po` (compiled `.mo` live next to them, git-ignored) |
| `assets/` | ✔ | Non-text assets: `font/`, `img/`, `icon/`, `scripts_datatables/`, `MM8Setup/`, `sound/`+`video/` (large, git-ignored) |
| `installer/` | ✔ | NSIS scripts (`nsi/<lang>/<target>/mm_i18n.nsi`) and per-installer additional files |
| `config/` | ✔ | All project configuration (see below) |
| `mm678i18n/` | ✔ | The Python build package (`mm678` CLI) |
| `vendor/` | ✔ | Third-party binaries: `mmarch.exe`, `TxtEdit/` |
| `references/` | ✔ | Translation reference material |
| `docs/` | ✔ | User documentation (GitHub Pages) + `docs/dev/` developer docs |
| `build/` | ✘ | ALL generated output — safe to delete at any time |

## Configuration (single source of truth)

- `config/languages.py` — per-language metadata: game encoding, source
  encoding, version, DBCS font sizes. **Everything language-specific derives
  from this file.**
- `config/versions.py` — GrayFace/Merge versions, installer release version,
  and the installer matrix (which lang × game targets get built).
- `config/settings.py` — text-pipeline settings (folders, template markers,
  quoting rules).

## Pipeline

```
                       mm678 <command>
┌────────────┐ templates ┌─────────────────┐  dev  ┌────────────┐
│ templates/ ├──────────►│ build/          ├──────►│ build/dev/ │ ◄─ Poedit
│ source/en  │           │ templates_ctx/  │       │ (.py files)│    scans this
└────────────┘           └─────────────────┘       └─────┬──────┘
                                                         │
        translations/<lang>/LC_MESSAGES/mm678.po  ◄──────┘ (translators edit .po)
                          │ mo
                          ▼
        translations/<lang>/LC_MESSAGES/mm678.mo
                          │ prod
                          ▼
              build/prod/<lang>/<game>/...        (translated game text)
                          │ postprod   + assets/ (fonts, scripts, img, sound)
                          ▼
              build/postprod/<lang>/<game>/...    (installable file tree,
                          │ installers             DBCS-encoded, .lod packed)
                          ▼
              build/setup/out/MM*.exe / .7z       (NSIS installers)
```

- **templates** (`mm678 templates`): adds translation-context markers
  (`_(TRANS_CONTEXT:'items')_`) to the context-less templates.
- **dev** (`mm678 dev`): matches `source/en` against the templates and emits
  one `.py` file per game text file, containing `_("...")`/`_x("ctx", "...")`
  calls. Poedit "Update from source code" scans these to refresh the `.po`.
- **mo** (`mm678 mo`): compiles every `.po` to `.mo` (polib — Poedit not
  needed for this).
- **prod** (`mm678 prod`): runs each dev `.py` with gettext translations to
  write the translated game text files in each language's game encoding.
- **postprod** (`mm678 postprod`): DBCS special encoding for CJK, font files,
  shared+per-language Lua scripts/data tables, images, sounds, MM8Setup, and
  packs `10 Loc*` folders into `.lod`/`.snd` archives with mmarch.
- **installers** (`mm678 installers`): composes each installer working dir,
  packs a portable extract-over-the-game-dir `.zip`, compiles the NSIS
  installers and 7-zips them. The `.zip` cannot delete files obsoleted by
  old patch versions — the installer's Delete list handles that.

`mm678 build` = mo + prod + postprod + installers.

## Single-source-of-truth rules

- Language metadata: only in `config/languages.py`.
- Files shared between languages/games are stored ONCE and distributed at
  build time:
  - `assets/scripts_datatables/_common/_all/` → every language × every game in
    `settings.script_games`; `_common/<game>/` → every language, that game.
    `FNT_DBCS.lua` is one canonical copy whose `fontSizes` line is patched
    per language from `config/languages.py`.
  - `assets/img/prod/<lang>/mmmerge_and_mm8/` → shipped to both mmmerge and
    mm8.
  - `installer/additional_files/zh/mm8/zh_update/` holds only the files that
    are NOT in `zh/`; the `mm8_zh_update` installer is composed as
    `zh` + `zh_update` (see `installers` in `config/versions.py`).

## Language derivation

- Which languages get `.po` generation: folders in `source/`.
- Which languages get built (mo/prod/postprod): `en` + folders in
  `translations/`. Adding a language = adding its `.po`
  (`mm678 new-language <lang>`).
