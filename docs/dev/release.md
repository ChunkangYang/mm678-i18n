# Release process

## Versions

All versions live in `config/`:

- `config/versions.py` — GrayFace patch versions, MM Merge version
  (date form), and `i18n_release` (`date` + `dot`), which is stamped into the
  installers via `makensis /DVERSION /DVERSIONDOT`.
- `config/languages.py` — per-language `i18n_version`.

## When MM Merge updates

1. Update `versions['merge']` (and GrayFace versions if changed) in
   `config/versions.py`.
2. Update `assets/scripts_datatables/` for ALL languages (diff against the
   new Merge scripts; shared files live in `_common/`).
3. If translatable text changed: update `source/en` + `templates/`, run
   `mm678 templates && mm678 dev`, update each `.po` in Poedit
   (*Update from source code*), translate new strings.
4. Update `i18n_release` in `config/versions.py`, write `CHANGELOG.md`, and
   update the player-facing changelog in `docs/zh/README.md`.
5. `mm678 check && mm678 build`.
6. If the installers' compose step prints a *FILE COPYING block differs*
   warning, review it and update the block in the affected
   `installer/nsi/<lang>/<target>/mm_i18n.nsi`.

## Publishing

1. Commit, tag `v<date or version>`, push with tags.
2. The GitHub Actions release workflow builds the installers on a Windows
   runner and attaches the `.7z` files to the GitHub Release. (Note:
   `assets/sound/` and `assets/video/` are not in git, so CI-built installers
   lack the voice-over archives — for zh releases, build locally with
   `mm678 build` and upload, or attach the sound archives separately.)
3. Update the download links / Baidu netdisk mirror referenced in
   `docs/zh/README.md` if needed.
