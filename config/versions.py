# Game/patch versions and the installer target matrix.
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

# Release identity of the language-patch installers themselves
# (used as NSIS VERSION / VERSIONDOT defines)
i18n_release = {
	'date': '2026-08-16',
	'dot': '2026.8.16.0',
}

# Which installers to build: one entry per produced setup .exe / extract-over .zip.
#   target      folder/name of the installer working dir under the setup dev dir
#   game        which postprod game tree goes in ('mm6'/'mm7'/'mm8'/'mmmerge')
#   icon        icon file (in the setup additional_files icons dir)
#   additional  additional-file trees (relative to the additional_files dir),
#               copied into the installer in order, before the postprod tree
#   outname     base name of the produced files; the release date is appended
#               (must match the OutFile naming in the target's mm_i18n.nsi)
installers = []
for _lang in ['zh_CN', 'zh_TW']:
	installers += [
		{'lang': _lang, 'target': 'mmmerge', 'game': 'mmmerge', 'icon': 'mmmerge.ico',
		 'additional': ['zh/mmmerge/zh'], 'outname': 'MMMerge_' + _lang},
		{'lang': _lang, 'target': 'mm8', 'game': 'mm8', 'icon': 'mm8.ico',
		 'additional': ['zh/mm8/zh'], 'outname': 'MM8_' + _lang},
		{'lang': _lang, 'target': 'mm8_zh_update', 'game': 'mm8', 'icon': 'mm8.ico',
		 'additional': ['zh/mm8/zh', 'zh/mm8/zh_update'], 'outname': 'MM8_' + _lang + '_Update'},
	]
