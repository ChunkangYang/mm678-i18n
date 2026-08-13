# Per-language metadata — the single source of truth.
#
# Fields per language:
#   encoding         encoding of the produced game files (and of the NSIS/ini
#                    metadata written for that language)
#   source_encoding  encoding of the files in the source folder for that
#                    language; omit for UTF-8 (e.g. fr sources were converted
#                    to UTF-8, unlike en/zh which are kept in game encoding)
#   i18n_version     version of this language's patch
#   fnt_dbcs_font_sizes
#                    for DBCS languages: the `local fontSizes = {...}` values
#                    patched into the shared Scripts/General/FNT_DBCS.lua

LANGUAGES = {
	'en':    {'encoding': 'cp1252', 'source_encoding': 'cp1252', 'i18n_version': '2.3'},
	'fr':    {'encoding': 'cp1252',                              'i18n_version': '2.3'},
	'de':    {'encoding': 'cp1252',                              'i18n_version': '2.3'},
	'es':    {'encoding': 'cp1252',                              'i18n_version': '2.3'},
	'it':    {'encoding': 'cp1252',                              'i18n_version': '2.3'},
	'ru':    {'encoding': 'cp1251',                              'i18n_version': '2.3'},
	'cs':    {'encoding': 'cp1250',                              'i18n_version': '2.3'},
	'pl':    {'encoding': 'cp1250',                              'i18n_version': '2.3'},
	'ko':    {'encoding': 'euc_kr',                              'i18n_version': '2.3'},
	'ja':    {'encoding': 'euc_jp',                              'i18n_version': '2.3'},
	'zh_CN': {'encoding': 'gb2312', 'source_encoding': 'gb2312', 'i18n_version': '2.3',
	          'fnt_dbcs_font_sizes': [13, 16, 29]},
	'zh_TW': {'encoding': 'big5',   'source_encoding': 'big5',   'i18n_version': '2.3',
	          'fnt_dbcs_font_sizes': [14, 16, 29]},
}

# Encodings that are double-byte character sets (need the DBCS special
# treatment in postprod and the FNT_DBCS.lua runtime support)
DBCS_ENCODINGS = ['gb2312', 'big5', 'euc_kr', 'euc_jp']


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
