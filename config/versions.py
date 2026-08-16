# Game/patch versions and the release matrix.
# Language-specific metadata (encodings, per-language versions) lives in
# config/languages.py — do not duplicate it here.

from config.languages import LANGUAGES, langEncDict, dbcsLangs, dbcsEncs  # noqa: F401 (re-exported)

versions = {
	'grayface': {
		'6': '2.5.7',
		'7': '2.5.7',
		'8': '2.5.7',
	},
	'merge': '2024-10-30',
	# per-language i18n version (last-update date, derived from languages.py)
	'i18n': {lang: meta['i18n_version'] for lang, meta in LANGUAGES.items()},
}

# Release identity of the language patches (the date goes into the
# release archive names)
i18n_release = {
	'date': '2026-08-16',
}

# Which release .zip archives to build: one entry per produced archive.
# Releases are PURE language packs - prerequisites like GrayFace patch and
# MMExtension are installed by the user from their official pages.
#   target      folder/name of the working dir under build/release/dev
#   game        which postprod game tree goes in ('mm6'/'mm7'/'mm8'/'mmmerge')
#   outname     base name of the produced .zip; the release date is appended
releases = []
for _lang in ['zh_CN', 'zh_TW']:
	releases += [
		{'lang': _lang, 'target': 'mmmerge', 'game': 'mmmerge', 'outname': 'MMMerge_' + _lang},
		{'lang': _lang, 'target': 'mm8', 'game': 'mm8', 'outname': 'MM8_' + _lang},
	]
