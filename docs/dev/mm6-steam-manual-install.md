# Installing a built MM6 language pack onto a standalone Steam install

This repo's release matrix (`config/versions.toml`) already produces
`MM6_<lang>_<date>.zip` release archives (`mm678 build --langs <lang>`), but
those archives only replace **text/fonts/scripts**. To get working Chinese
(or any DBCS-language) text on screen in a *standalone* Steam copy of Might
and Magic VI, three separate things have to be installed, in order, onto the
same game folder — none of this is unique to Chinese, it applies to any
`native_dbcs_games` language:

1. **GrayFace MM6 Patch** — the engine patch itself (bugfixes, hooks, the
   `ExeMods` loader). Without it there is no `FNT_DBCS.lua` runtime at all.
2. **MMExtension** — the Lua scripting engine that GrayFace's patch loads
   through its `ExeMods` folder. `FNT_DBCS.lua` (the script that actually
   renders double-byte glyphs) does nothing without this — its absence is
   the single most common cause of garbled/mojibake text after installing
   only the GrayFace patch and the language pack.
3. **This repo's built language pack** (`MM6_<lang>_<date>.zip` or the
   `build/postprod/<lang>/mm6/` tree copied directly).

Order 1 → 2 → 3 matters: MMExtension's `ExeMods/` and `Scripts/` folders
must exist before the language pack's own `Scripts/General/FNT_DBCS.lua`
and `ProgramName.lua` are dropped in (they merge into the same `Scripts/`
tree without conflict — MMExtension ships its own `Scripts/Core`,
`Scripts/General/DataTables.lua` etc.; the language pack only adds two
files under `Scripts/General/`).

## Prerequisites

- A Steam (or any) MM6 install with `mm6.exe` present (if it's missing,
  Steam's "verify integrity of game files" restores it)
- 7-Zip or any tool that can extract `.rar` (MMExtension ships as `.rar`)
- This repo built for your language: `mm678 build --langs <lang>` (see
  [building.md](building.md)); or at minimum
  `mm678 build --no-release --langs <lang>` to get `build/postprod/<lang>/mm6/`

## Steps

### 1. Install the GrayFace MM6 Patch

Check `config/versions.toml` → `[grayface_versions]` → `6` for the exact
version this repo's build targets (mismatched versions may still work, but
match them to be safe).

Download from the official page (https://grayface.github.io/mm/#GrayFace-MM6-Patch),
e.g. for v2.5.7:
`https://github.com/GrayFace/Misc/releases/download/MM6Patch-2.5.7/MM6.Patch.v2.5.7.exe`

It's an Inno Setup installer, so it can be run unattended:

```powershell
Start-Process -FilePath MM6.Patch.v2.5.7.exe -ArgumentList `
  "/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART","/DIR=`"<game dir>`"" `
  -Wait
```

This renames the original `mm6.exe` (if not already renamed) and drops in
the patched one, plus `MM6patch.dll` and `MM6Patch ReadMe.TXT`.

### 2. Install MMExtension

Download from https://grayface.github.io/mm/ext (MMExtension v2.2, ships
as a `.rar`, currently hosted on Dropbox — link may change, check the page).

Extract it, then copy (merge, don't overwrite) its `ExeMods/` and
`Scripts/` folders into the game directory:

```powershell
robocopy "<extracted>\ExeMods"  "<game dir>\ExeMods"  /E
robocopy "<extracted>\Scripts"  "<game dir>\Scripts"  /E
```

(`robocopy /E` merges directories and won't touch files not present in the
source, so anything already in `<game dir>\Scripts` — including files the
step 3 language pack already dropped there, if you do this out of order —
is left alone.)

### 3. Apply the language pack

Either extract the built release zip over the game directory, or, from the
repo root, if you already ran `mm678 build --no-release --langs <lang>`:

```
mm678 apply <lang> mm6 "<game dir>"
```

### 4. First run

The first launch after MMExtension is installed pops up a dialog:
*"MMExtension is about to generate text tables for binary files. This will
take a few minutes. On the next run of the game you will also experience a
delay."* — this is normal, one-time, click OK and wait. It does not
reappear on subsequent launches.

## Verifying / troubleshooting

- **Garbled/mojibake text instead of readable CJK** → MMExtension isn't
  installed or isn't loading. Check `<game dir>\ExeMods\MMExtension.dll`
  exists.
- Add `nativelog=1` under `[Settings]` in `<game dir>\data\LocalizeConf.ini`
  to make the renderer write `FNT_DBCS.log` into the game folder — see
  [fonts.md](fonts.md) for what it records.
- **Some hover labels stay in English even with fully translated `.po`**
  (e.g. torches, trees, some generic/unnamed NPCs, some decorative map
  objects) — these strings are hardcoded in the engine binary or baked
  into map files, not sourced from the translatable text tables this
  pipeline covers. This is a known upstream limitation (see
  [TODO.md](TODO.md) → "Untranslated / display bugs"), not a broken
  install — it affects the original game's other languages too.

## Automating it

`tools/install_mm6_lang.ps1` in this repo scripts steps 1–3 above (download
+ silent-install GrayFace patch, download + merge MMExtension, apply the
built package) given a game directory and language code.
