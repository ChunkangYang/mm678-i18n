# Quality checks: po validity, source-file encodings, stray LF line endings,
# postprod line lengths. `mm678 check` runs everything that is applicable.
# Each check returns the number of problems found (0 = pass).

import re
from pathlib import Path

import polib

from . import paths  # noqa: F401
from .getfilepaths import getFilePaths
from config import settings
from config.languages import LANGUAGES, langEncDict, dbcsLangs


# ---- po files ----

def checkPoFiles():
	problems = 0
	i18nPath = Path(settings.i18n_folder)
	for p in sorted(i18nPath.glob('*/LC_MESSAGES/' + settings.textdomain + '.po')):
		try:
			po = polib.pofile(str(p))
			print('OK   ' + str(p) + '  (' + str(len(po)) + ' entries, ' +
			      str(po.percent_translated()) + '% translated)')
		except Exception as e:
			problems += 1
			print('FAIL ' + str(p) + ': ' + str(e))
	return problems


# ---- file encodings ----

def validateFileEncoding(pathObj, inputEncoding, outputEncoding = None):
	f = pathObj.open(mode = 'r', encoding = inputEncoding, errors = "strict")
	content = f.read()
	f.close()
	if outputEncoding != None:
		content.encode(outputEncoding)


def checkSourceEncodings():
	problems = 0
	sourcePath = Path(settings.source_folder)
	for langDir in sorted(getFilePaths(sourcePath, '', False)):
		lang = langDir.name
		encoding = settings.source_encoding.get(lang, 'UTF-8')
		for p in getFilePaths(langDir, settings.file_extensions):
			try:
				validateFileEncoding(p, encoding)
			except Exception as e:
				problems += 1
				print('FAIL ' + str(p) + ' is not valid ' + encoding + ': ' + str(e))
		# custom word lists are always UTF-8
		for p in getFilePaths(langDir, 'list'):
			try:
				validateFileEncoding(p, 'UTF-8')
			except Exception as e:
				problems += 1
				print('FAIL ' + str(p) + ' is not valid UTF-8: ' + str(e))
	if problems == 0:
		print('OK   all source files decode with their configured encodings')
	return problems


# ---- stray LF (non-CRLF) line endings in source files ----

def checkLf(path, encoding = None):
	problems = 0
	f = path.open(mode = 'r', newline = '\r\n', encoding = encoding, errors = 'replace')
	for i, line in enumerate(f):
		found = len(re.findall('(?<!\r)\n', line))
		if found != 0:
			problems += 1
			print('FAIL ' + str(found) + ' bare LF found in line ' + str(i + 1) + ' of ' + str(path))
	f.close()
	return problems


def checkSourceLf():
	problems = 0
	sourcePath = Path(settings.source_folder)
	for langDir in sorted(getFilePaths(sourcePath, '', False)):
		encoding = settings.source_encoding.get(langDir.name, 'UTF-8')
		for p in getFilePaths(langDir, ['txt', 'str']):
			problems += checkLf(p, encoding)
	if problems == 0:
		print('OK   no bare LF line endings in source txt/str files')
	return problems


# ---- postprod line length (game engine limit) ----

MAX_STR_LINE_BYTES = 784

def checkLineLength():
	problems = 0
	postprodPath = Path(settings.postprod_folder)
	if not postprodPath.exists():
		print('SKIP line-length check: ' + str(postprodPath) + ' does not exist (run postprod first)')
		return 0
	for lang in dbcsLangs:
		langPath = postprodPath.joinpath(lang)
		if not langPath.exists():
			continue
		encoding = langEncDict[lang]
		for p in getFilePaths(langPath, 'str'):
			f = p.open(mode = 'rb')
			for n, line in enumerate(f.read().split(b'\r\n')):
				if len(line) > MAX_STR_LINE_BYTES:
					problems += 1
					print('FAIL line ' + str(n + 1) + ' of ' + str(p) + ' is ' + str(len(line)) +
					      ' bytes (limit ' + str(MAX_STR_LINE_BYTES) + ')')
			f.close()
	if problems == 0:
		print('OK   no over-long lines in postprod .str files')
	return problems


CHECKS = {
	'po': checkPoFiles,
	'encoding': checkSourceEncodings,
	'lf': checkSourceLf,
	'linelength': checkLineLength,
}

# 'lf' is diagnostic only: bare LF inside translatable strings is legitimate
# (soft line breaks, handled by lf_in_crlf_mode), so it is not run by default
DEFAULT_CHECKS = ['po', 'encoding', 'linelength']


def run(names = None):
	problems = 0
	for name in (names or DEFAULT_CHECKS):
		print('== check: ' + name + ' ==')
		problems += CHECKS[name]()
	if problems:
		print(str(problems) + ' problem(s) found.')
	else:
		print('All checks passed.')
	return problems
