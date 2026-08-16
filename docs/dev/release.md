# Release process

## Versions

All versions live in `config/`:

- `config/versions.toml` — GrayFace patch versions, MM Merge version
  (date form), and `release_date` (which goes into the release
  archive names).
- `config/languages.toml` — per-language `i18n_version`.

## When MM Merge updates

1. Update `merge_version` (and `grayface_versions` if changed) in
   `config/versions.toml`.
2. Update `assets/scripts_datatables/` for ALL languages (diff against the
   new Merge scripts; shared files live in `_common/`).
3. If translatable text changed: update `source/en` + `templates/`, run
   `mm678 templates && mm678 dev`, update each `.po` in Poedit
   (*Update from source code*), translate new strings.
4. Update `release_date` in `config/versions.toml`, write `CHANGELOG.md`, and
   update the player-facing changelog in `docs/zh/README.md`.
5. `mm678 check && mm678 build` — produces the extract-over release `.zip`
   archives in `build/release/out/` (matrix: `releases` in
   `config/versions.toml`).

## Publishing

1. Commit, tag `v<date or version>`, push with tags.
2. The GitHub Actions release workflow builds the release zips on a Windows
   runner and attaches them to the GitHub Release. (Note: `assets/sound/`
   and `assets/video/` are not in git, so CI-built archives lack the
   voice-over content — for zh releases, build locally with `mm678 build`
   and upload, or attach the sound archives separately.)
3. Update the download links / Baidu netdisk mirror referenced in
   `docs/zh/README.md` if needed.
