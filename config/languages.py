# Per-language metadata — the single source of truth.
#
# Fields per language:
#   encoding         encoding of the produced game files (and of the NSIS/ini
#                    metadata written for that language)
#   source_encoding  encoding of the files in the source folder for that
#                    language; omit for UTF-8 (e.g. fr sources were converted
#                    to UTF-8, unlike en/zh which are kept in game encoding)
#   i18n_version     version of this language's patch
#   dbcs_fonts       for DBCS languages: the BDF font per engine font name
#                    (shipped into Data\DBCSFonts\ and filled into the built
#                    LocalizeConf.ini's [dbcsFont] section)


# Assignment rule (per host font height, measured heights in docs/dev/fonts.md):
# >= 25 (Book, Cchar, Book2) -> the 24px font; >= 16 (Lucida..Comic,
# Autonote, Spell) -> the 14px font; below (Smallnum) and Default -> the 12px
# font. The renderer auto-crops each BDF's blank canvas rows and anchors the
# glyph one pixel below the host font's baseline; a trailing ",N" flag would
# add N px of line spacing for that font only (none needed by default).
def _dbcs_fonts(f12, f14, f24):
	fonts = {name: f14 for name in
	         ['Lucida', 'Arrus', 'Create', 'Comic', 'Autonote', 'Spell']}
	# ",1" = one extra pixel of line spacing for the dense 12px-font hosts
	fonts.update({'Default': f12 + ',1', 'Smallnum': f12 + ',1',
	              'Book': f24, 'Cchar': f24, 'Book2': f24})
	return fonts


LANGUAGES = {
	'en':    {'encoding': 'cp1252', 'source_encoding': 'cp1252', 'i18n_version': '2.3'},
	'fr':    {'encoding': 'cp1252',                              'i18n_version': '2.3'},
	'de':    {'encoding': 'cp1252',                              'i18n_version': '2.3'},
	'es':    {'encoding': 'cp1252',                              'i18n_version': '2.3'},
	'it':    {'encoding': 'cp1252',                              'i18n_version': '2.3'},
	'ru':    {'encoding': 'cp1251',                              'i18n_version': '2.3'},
	'cs':    {'encoding': 'cp1250',                              'i18n_version': '2.3'},
	'pl':    {'encoding': 'cp1250',                              'i18n_version': '2.3'},
	'ko':    {'encoding': 'euc_kr',                              'i18n_version': '2.3',
	          'dbcs_fonts': _dbcs_fonts('fusion-pixel-12px-ko.bdf',
	                                    'Galmuri14.bdf',
	                                    'LXGWWenKaiKR-Medium-24px.bdf')},
	'ja':    {'encoding': 'shift_jis',                           'i18n_version': '2.3',
	          'dbcs_fonts': _dbcs_fonts('fusion-pixel-12px-ja.bdf',
	                                    'Shinonome-14px.bdf',
	                                    'KleeOne-SemiBold-24px.bdf')},
	'zh_CN': {'encoding': 'gb2312', 'source_encoding': 'gb2312', 'i18n_version': '2.3',
	          'dbcs_fonts': _dbcs_fonts('fusion-pixel-12px-zh_hans.bdf',
	                                    'wenquanyi_14px.bdf',
	                                    'LXGWWenKaiGB-Medium-24px.bdf')},
	'zh_TW': {'encoding': 'big5',   'source_encoding': 'big5',   'i18n_version': '2.3',
	          'dbcs_fonts': _dbcs_fonts('fusion-pixel-12px-zh_hant.bdf',
	                                    'wenquanyi_14px.bdf',
	                                    'LXGWWenKaiTC-Medium-24px.bdf')},
}

# Encodings that are double-byte character sets (rendered by the native
# FNT_DBCS.lua runtime). Japanese uses shift_jis (the game-world standard;
# note: half-width katakana is not supported - use full-width kana).
DBCS_ENCODINGS = ['gb2312', 'big5', 'euc_kr', 'shift_jis']

# Languages with no tracked .po of their own: their .po is regenerated at
# build time from another language's .po (target -> (source, OpenCC method)).
# zh_TW is always derived from zh_CN, so only zh_CN gets translated by hand.
DERIVED_LANGUAGES = {'zh_TW': ('zh_CN', 's2twp')}


# ---- derived tables (import these instead of rebuilding them) ----

# game-file encoding per language (formerly tools/versions.py langEncDict)
langEncDict = {lang: meta['encoding'] for lang, meta in LANGUAGES.items()}

# DBCS language list (formerly tools/versions.py dbcsLangs)
dbcsLangs = [lang for lang, meta in LANGUAGES.items() if meta['encoding'] in DBCS_ENCODINGS]

# alias kept for readability at call sites
dbcsEncs = DBCS_ENCODINGS

# source-folder encoding per language where it is not UTF-8
# (formerly settings.py source_encoding)
source_encoding = {
	lang: meta['source_encoding']
	for lang, meta in LANGUAGES.items() if 'source_encoding' in meta
}
