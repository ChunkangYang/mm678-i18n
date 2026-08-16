# Per-language metadata — the single source of truth.
# The data half lives in languages.toml; this module loads it and derives
# the lookup tables. Import the tables below instead of parsing the TOML.

import tomllib
from pathlib import Path

with open(Path(__file__).with_name('languages.toml'), 'rb') as _f:
	_data = tomllib.load(_f)


# Engine-font assignment rule (per host font height, measured heights in
# docs/dev/fonts.md): >= 25 (Book, Cchar, Book2) -> the 24px font; >= 16
# (Lucida..Comic, Autonote, Spell) -> the 14px font; below (Smallnum) and
# Default -> the 12px font. The renderer auto-crops each BDF's blank canvas
# rows and anchors the glyph one pixel below the host font's baseline; a
# trailing ",N" flag would add N px of line spacing for that font only
# (none needed by default).
def _dbcs_fonts(f12, f14, f24):
	fonts = {name: f14 for name in
	         ['Lucida', 'Arrus', 'Create', 'Comic', 'Autonote', 'Spell']}
	# ",1" = one extra pixel of line spacing for the dense 12px-font hosts
	fonts.update({'Default': f12 + ',1', 'Smallnum': f12 + ',1',
	              'Book': f24, 'Cchar': f24, 'Book2': f24})
	return fonts


# per-language metadata dict; the TOML's f12/f14/f24 triple is expanded
# into the per-engine-font map here
LANGUAGES = {}
for _lang, _meta in _data['languages'].items():
	_meta = dict(_meta)
	if 'dbcs_fonts' in _meta:
		_bdf = _meta['dbcs_fonts']
		_meta['dbcs_fonts'] = _dbcs_fonts(_bdf['f12'], _bdf['f14'], _bdf['f24'])
	LANGUAGES[_lang] = _meta

DBCS_ENCODINGS = _data['dbcs_encodings']

# target -> (source language, OpenCC method); see languages.toml
DERIVED_LANGUAGES = {
	lang: (spec['source'], spec['opencc_method'])
	for lang, spec in _data.get('derived_languages', {}).items()
}


# ---- derived tables (import these instead of rebuilding them) ----

# game-file encoding per language
langEncDict = {lang: meta['encoding'] for lang, meta in LANGUAGES.items()}

# DBCS language list
dbcsLangs = [lang for lang, meta in LANGUAGES.items() if meta['encoding'] in DBCS_ENCODINGS]

# alias kept for readability at call sites
dbcsEncs = DBCS_ENCODINGS

# source-folder encoding per language where it is not UTF-8
source_encoding = {
	lang: meta['source_encoding']
	for lang, meta in LANGUAGES.items() if 'source_encoding' in meta
}
