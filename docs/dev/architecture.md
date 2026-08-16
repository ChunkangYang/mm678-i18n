# Architecture

The project turns the games' original text files plus gettext translations
into per-language patch packages.

## Repository layout

| Path | Tracked | What it is |
|---|---|---|
| `source/` | ✔ | Original game text files per language (`en/` is the reference; other folders hold pre-existing translated game files used only to seed a language) |
| `templates/` | ✔ | Game text files with every translatable cell replaced by `_(TRANS)_` |
| `translations/` | ✔ | gettext files: `mm678.pot` + `<lang>/mm678.po` (compiled `.mo` live next to them, git-ignored) |
| `assets/` | ✔ | Non-text assets: `font/`, `img/`, `icon/`, `scripts_datatables/`, `MM8Setup/`, `sound/`+`video/` (large, git-ignored) |
| `config/` | ✔ | All project configuration (see below) |
| `mm678i18n/` | ✔ | The Python build package (`mm678` CLI) |
| `references/` | ✔ | Translation reference material |
| `docs/` | ✔ | User documentation (GitHub Pages) + `docs/dev/` developer docs |
| `build/` | ✘ | ALL generated output — safe to delete at any time |

## Configuration (single source of truth)

Each area is a `.toml` (the editable data) plus a same-named `.py` that
loads it and derives the lookup tables the pipeline imports:

- `config/languages.toml` — per-language metadata: game encoding, source
  encoding, version, DBCS fonts. **Everything language-specific derives
  from this file.**
- `config/versions.toml` — GrayFace/Merge versions, the release version,
  and the release matrix (which lang × game targets get built).
- `config/settings.toml` — text-pipeline settings (folders, template markers,
  quoting rules).

## Pipeline

```
                       mm678 <command>
┌────────────┐ templates ┌─────────────────┐  dev  ┌────────────┐
│ templates/ ├──────────►│ build/          ├──────►│ build/dev/ │ ◄─ Poedit
│ source/en  │           │ templates_ctx/  │       │ (.py files)│    scans this
└────────────┘           └─────────────────┘       └─────┬──────┘
                                                         │
        translations/<lang>/mm678.po  ◄──────┘ (translators edit .po)
                          │ mo
                          ▼
        translations/<lang>/mm678.mo
                          │ prod
                          ▼
              build/prod/<lang>/<game>/...        (translated game text)
                          │ postprod   + assets/ (fonts, scripts, img, sound)
                          ▼
              build/postprod/<lang>/<game>/...    (installable file tree,
                          │ release                DBCS-encoded, .lod packed)
                          ▼
              build/release/out/MM*.zip             (release archives)
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
- **release** (`mm678 release`): composes each release working dir,
  packs an extract-over-the-game-dir `.zip`. The `.zip` cannot delete
  files obsoleted by very old patch versions; leftovers are harmless
  (name-sort losers) — see the cleanup note in `docs/dev/TODO.md`.

`mm678 build` = mo + prod + postprod + release.

## Single-source-of-truth rules

- Language metadata: only in `config/languages.py`.
- Files shared between languages/games are stored ONCE and distributed at
  build time:
  - `assets/scripts_datatables/_common/_all/` → every language × every game in
    `settings.script_games`; `_common/<game>/` → every language, that game.
    `FNT_DBCS.lua` is one canonical copy; per-language BDF font mappings come
    from `dbcs_fonts` in `config/languages.py` and are both filled into
    `LocalizeConf.ini`'s `[dbcsFont]` section and shipped (with the
    encoding's `.tbl`) into `Data\DBCSFonts\`.
    Renderer + font configuration reference: `docs/dev/fonts.md`.
  - `assets/img/prod/<lang>/mmmerge_and_mm8/` → shipped to both mmmerge and
    mm8.
  
## Language derivation

- Which languages get `.po` generation: folders in `source/`.
- Which languages get built (mo/prod/postprod): `en` + folders in
  `translations/`. Adding a language = adding its `.po`
  (`mm678 new-language <lang>`).
