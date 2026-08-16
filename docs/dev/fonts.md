# Fonts & the native DBCS renderer

`assets/scripts_datatables/_common/_all/Scripts/General/FNT_DBCS.lua` renders
double-byte text (Chinese/Japanese/Korean) natively in MM6/MM7/MM8/Merge:
plain DBCS bytes in the game files, CJK-aware word wrap with kinsoku rules
(line-start/line-end prohibition tables for gb2312/gbk, big5 and shift_jis —
closers/small kana hang at line end, openers get pushed down; euc_kr text
mostly uses single-byte punctuation, which wraps like Western text),
glyphs from BDF fonts or legacy page fonts. It activates automatically when
`Data/LocalizeConf.ini`'s `[Settings]` `encoding` is one of `gb2312`, `gbk`,
`big5`, `shift_jis`, `euc_kr` (shift_jis caveat: half-width katakana is not
supported — use full-width kana).

## LocalizeConf.ini reference

All parsers are section-aware: keys only count inside their `[section]`.

### `[Settings]`

| key | meaning |
|---|---|
| `encoding` | game text encoding; a supported DBCS value activates the renderer |
| `program_name` | localized window/program name, stored in UTF-8. `ProgramName.lua` converts it to the user's **system** codepage (GetACP; DBCS via the `.tbl` tables, cp1252 direct, system-UTF-8 passes through) for the engine's ANSI buffer (19-byte limit on MM6, 23 on MM7/8) and re-sets the window title with `SetWindowTextW` in real Unicode, so it displays correctly on any locale. A non-UTF-8 value is used as raw bytes (legacy format) |
| `lineSpacing` | extra pixels between text lines, 0–10 (the engines lay lines out at `fontHeight−3`, which full-canvas CJK glyphs can touch across; the pipeline writes `2`). Global: applies to every font and all multi-line text, Latin included; single lines are unaffected. Patches every layout site — drawing and height measurement move together, so dialog boxes grow to match |
| `fontSizes` | legacy page-font heights when they differ from the built-in `13,16,29`; only relevant if you ship page fonts yourself (builds are BDF-only) |
| `specialFonts` | legacy page-font per-font override, e.g. `Autonote:15b` (same caveat) |
| `nativedemo=1` | debug: shows a plain-DBCS test message in-game (used to smoke-test new engines) |
| `nativelog=1` | debug: writes `FNT_DBCS.log` diagnostics into the game folder |

The debug keys are never written into shipped inis.

### `[dbcsFont]` — BDF font mapping

BDF files live in `Data\DBCSFonts\`. Each line maps an engine font by name;
the shipped template contains every line with an empty value (= not
configured) plus a comment with the font's measured height/style.

```ini
[dbcsFont]
Default=wqy12.bdf,wqy16.bdf
Arrus=wqy16.bdf
Autonote=wqy16.bdf
Comic=wqy16.bdf,plain,-1
```

Comma-separated tokens after the key are classified as:

- **file name** — the BDF to use. Named lines take one file; `Default` takes
  one or more, and any font without its own line picks from them **by
  height** (largest BDF that fits the font's height, else the smallest).
- **style flag** `shadow` / `plain` / `black` — overrides the style.
  Without a flag the style is **auto-detected from the host game font's own
  glyph pixels**, so `Autonote=x.bdf` automatically renders black and a bare
  `Default=` line styles every font correctly. The three styles (facts
  measured from the shipped fonts): `shadow` = body 255 + value-1 drop
  shadow offset (+1,+1) — most fonts; `plain` = body 255 only — Spell;
  `black` = body value 1 only — Autonote.
- **integer** — extra line spacing for THIS font, 0–10 px (e.g.
  `Smallnum=fusion-pixel-12px-zh_hans.bdf,2`). At runtime the engine font is
  heightened by N and its glyphs relocated into padded copies, so all layout
  paths (drawing, height measurement, dialog sizing) space this font's lines
  N px further apart while every other font keeps its spacing. Stacks with
  the global `[Settings] lineSpacing`. Vertical glyph placement itself is
  always automatic: the CJK glyph's bottom sits one row below the host
  font's baseline (sampled from its 0-9/A-Z glyphs).

Independent of any flag, blank canvas rows a BDF declares around its actual
ink are cropped away at load: the renderer measures the font's **ink band**
across all glyphs (if one extent covers ≥ 2/3 of the glyphs it wins —
pixel-font design boxes; otherwise the union of all extents — rasterized
fonts), emits only those rows, and bottom-anchors the result. Fonts whose
declared baseline contradicts their glyphs (e.g. `FONT_ASCENT` = height but
glyphs descend below it) are healed per glyph by shifting the overflow back
inside the canvas. Width/advance (`DWIDTH`) is never affected.

Resolution order per font: its own line → the `Default` list → legacy page
fonts (`DBCS_<size>_<hi>.fnt`, one file per lead byte per size, looked up in
the loaded LODs). Builds no longer ship page fonts — the BDF mapping covers
every font — but the page path still works if a mod supplies such files.

### Encoding table

BDF glyphs are keyed by Unicode, so each encoding needs a mapping table
`Data\DBCSFonts\<encoding>.tbl` — a flat little-endian u16 array over the
valid (lead, trail) byte ranges. All four live in `assets/font/`
(`gb2312.tbl`, `big5.tbl`, `shift_jis.tbl`, `euc_kr.tbl`); regenerate with:

```
python tools/gen_dbcstbl.py gb2312 assets/font/gb2312.tbl
```

The ranges in `gen_dbcstbl.py` must mirror `encProps` in `FNT_DBCS.lua`.
(shift_jis note: cp932's user-defined lead bytes F0–F9 map to Unicode
private-use codepoints — those cells are "mapped" but no font has glyphs
for them, which is correct: they render as missing.)

## Shipped BDF fonts

The `.bdf` files live flat in `assets/font/` (pixel fonts are used as-is;
the 16px/28px ones were rasterized from TTF/OTF as a one-off with
`tools/ttf2bdf.py`, see below — the TTF/OTF sources are not kept in the
repo). The per-language mapping is `dbcs_fonts` in `config/languages.py` —
the single source of truth the pipeline both copies files from and fills
the ini template with. Assignment rule by host font height:

| host height | zh_CN | zh_TW | ja | ko |
|---|---|---|---|---|
| ≥ 25 (Book, Cchar, Book2) | LXGWWenKaiGB-Medium-24px | LXGWWenKaiTC-Medium-24px | KleeOne-SemiBold-24px | LXGWWenKaiKR-Medium-24px |
| ≥ 16 (Spell…Comic) | wenquanyi_14px | wenquanyi_14px | Shinonome-14px | Galmuri14 |
| < 16 (Smallnum) + Default | fusion-pixel-12px-zh_hans | fusion-pixel-12px-zh_hant | fusion-pixel-12px-ja | fusion-pixel-12px-ko |

No flags are needed: the automatic ink-band crop reduces fusion-pixel's
declared 12×16 canvas to its true 12px design, and the automatic bottom
gap aligns every font with the host font's own padding.

Coverage caveats (measured against each language's `.tbl` charset): the
zh/ja sets miss only symbols outside game text (math signs, pinyin tone
marks, bopomofo tones); `neodgm` has no hanja (Korean 16px hanja would
render missing — hangul is complete); a named font's missing glyph does
**not** fall through to another BDF.

### tools/ttf2bdf.py — rasterizing TTF/OTF sources

```
python tools/ttf2bdf.py LXGWWenKaiGB-Medium.ttf 24 LXGWWenKaiGB-Medium-24px.bdf gb2312.tbl
```

Needs `pip install freetype-py`. Renders monochrome at the given pixel
size, restricted to the codepoints of the listed `.tbl` file(s) (so the
BDF only carries glyphs the game can request), fixes the canvas to
`px` with the face's ascent as the baseline, and keeps blank glyphs
(e.g. U+3000) as 1×1 empty bitmaps so the advance is preserved. The
generated 16px/28px BDFs are committed in `assets/font/`.

## Engine font facts (identical files across MM6/7/8)

| font | height | style | typical use |
|---|---|---|---|
| Smallnum | 14 | shadow | smallest UI font |
| Spell | 16 | plain | spellbook |
| Lucida | 17 | shadow | status bar |
| Create | 18 | shadow | character creation |
| Autonote | 18 | black | autonotes |
| Arrus | 19 | shadow | main dialog font |
| Comic | 19 | shadow | |
| Book | 25 | shadow | book headings |
| Cchar | 29 | shadow | credits (MM6/MM7) |
| Book2 | 30 | shadow | large titles |

## .fnt format (for reference)

| offset | type | field |
|---|---|---|
| `+0x00` | u1 | MinChar |
| `+0x01` | u1 | MaxChar |
| `+0x05` | u1 | Height |
| `+0x08` | i4 | PalettesCount |
| `+0x0C` | i4×5 | palette slots (pointers after load) |
| `+0x20` | (i4×3)×256 | ABC per char: spaceBefore, width, spaceAfter |
| `+0xC20` | i4×256 | glyph offsets (relative to `+0x1020`) |
| `+0x1020` | bytes | glyph bitmaps, one byte per pixel (0 transparent, 255 body, 1 shadow) |

Per-char advance = A (not for the line's first char) + B + C.

## Testing

`python tools/fnt_dbcs_harness/run.py` (needs `pip install lupa`) runs five
offline passes against the real Lua file: MM8 functional, MM7 install
sanity, MM6 install sanity, BDF-mode functional, and big5/shift_jis kinsoku
(fake mem/Game/fonts). Run it after any change to `FNT_DBCS.lua`.

For in-game debugging set `nativelog=1` (and optionally `nativedemo=1`) in
`[Settings]` and read `FNT_DBCS.log` in the game folder: it records every
install step, font-to-BDF resolution (with detected style), page/BDF loads
and any caught handler errors.

## Pipeline touchpoints

- `settings.native_dbcs_games` — which game trees ship plain DBCS text and
  get the `[dbcsFont]` template appended to their `LocalizeConf.ini`
  (template text: `DBCS_FONT_TEMPLATE` in `mm678i18n/postprod.py`, values
  filled from `languages.dbcs_fonts`).
- `copyDbcsFonts` in `mm678i18n/postprod.py` ships the language's BDF
  files + `<encoding>.tbl` from `assets/font/` into `Data\DBCSFonts\`
  (a plain folder, not packed into a LOD).
