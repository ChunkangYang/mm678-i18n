# Occasional maintenance helpers (not part of the regular build):
# - batchConvertLf:        convert '\n' escapes <-> bare LF in list files
# - restoreNormalizedLf:   re-join wrongly split CRLF lines in a numbered table
# - batchAddTransTemplate: help create template files from source game files
# - overwriteInPo:         batch-overwrite .po msgstr from a TSV table
#
# All are plain functions; import and call them from a Python shell, e.g.
#   python -c "from mm678i18n import maintenance; maintenance.overwriteInPo(...)"

import re
from pathlib import Path

import polib

from . import paths  # noqa: F401
from .getfilepaths import getFilePaths


# ---- LF conversion (originally tools/convert_lf.py) ----

def convertLf(inputPath, outputPath, encoding = None, SlashNTolf = True):
	f = inputPath.open(mode = 'r', newline = '\r\n', encoding = encoding)
	content = f.read()
	f.close()
	if SlashNTolf:
		content = re.sub(r'\\n', '\n', content)
	else:
		content = re.sub('(?<!\r)\n', r'\\n', content)
	outputPath.parent.mkdir(parents = True, exist_ok = True)
	fo = outputPath.open(mode = 'w', newline = '', encoding = encoding)
	fo.write(content)
	fo.close()


def batchConvertLf(inputPath, outputPath, SlashNTolf = True, extension = 'txt', encoding = 'UTF-8'):
	for p in getFilePaths(inputPath, extension = extension):
		convertLf(p, outputPath.joinpath(p.relative_to(inputPath)), encoding, SlashNTolf)


# ---- restore normalized LF (originally tools/restore_normalized_lf.py) ----
# For a table whose lines start with an increasing line number: any physical
# line NOT starting with the expected number belongs to the previous line, so
# the previous CRLF is turned back into a bare LF.

def restoreNormalizedLf(inputPath, outputPath, encoding = 'cp1252'):
	f = Path(inputPath).open(mode = 'r', newline = '\r\n', encoding = encoding)
	lines = f.readlines()
	f.close()
	lineNumber = 1
	for n, l in enumerate(lines):
		if re.match(str(lineNumber), l) == None:
			lines[n - 1] = lines[n - 1].replace('\r\n', '\n')
		else:
			lineNumber += 1
	fo = Path(outputPath).open(mode = 'w', newline = '', encoding = encoding)
	fo.writelines(lines)
	fo.close()


# ---- template creation helper (originally tools/template_helper.py) ----

TEMPLATE_KEEP_AS_IS = [
	r'^\d+$', r'^\s+$', r'^""$',
	r'^Placeholder$', r'^Placeholder Text$', r'^Enter$',
	r'^NPCText$', r'^TransTxt$', r'^ClassNames$', r'^NPCTopic$',
	r'^ItemsTxt$', r'^GlobalTxt$', r'^MonstersTxt$',
]

def addTransTemplate(path, skipRowNumber, inputPath, outputPath, encoding = 'cp1252', log = print):
	f = path.open(mode = 'r', newline = '\r\n', encoding = encoding)
	p2 = outputPath.joinpath(path.relative_to(inputPath))
	p2.parent.mkdir(parents = True, exist_ok = True)
	f2 = p2.open(mode = 'w', newline = '')

	regex = '(?<=\t)[^\t^\r]+(?=\t|\r\n|$)'
	regex2 = '(?<=^)[^\t^\r]+(?=\t|\r\n|$)'

	def repl(g, i):
		s = g.group(0)
		if any(re.match(r, s, re.IGNORECASE) for r in TEMPLATE_KEEP_AS_IS):
			return s
		elif re.match(r'^[^\d]+\d+$', s) != None or re.search(r'_', s) != None:
			log('"' + s + '" skipped in line ' + str(i) + ' of file ' + str(path))
			return s
		else:
			return '_(TRANS)_'

	for i, line in enumerate(f):
		if i < skipRowNumber:
			newline = line
		else:
			newline = re.sub(regex, lambda g: repl(g, i), line)
			newline = re.sub(regex2, lambda g: repl(g, i), newline)
		f2.write(newline)
	f.close()
	f2.close()


def batchAddTransTemplate(inputPath, outputPath, extList = 'txt', skipRowDict = {}, encoding = 'cp1252'):
	# skipRowDict: {file name: number of leading rows to skip} (default 1)
	for filePath in getFilePaths(inputPath, extList):
		skipRow = skipRowDict.get(str(filePath), 1)
		addTransTemplate(filePath, skipRow, inputPath, outputPath, encoding)


# ---- po batch overwrite (originally tools/overwrite_in_po.py) ----
# tablePath: UTF-8 TSV with columns msgctxt<TAB>msgid<TAB>msgstr
# (no duplicated msgctxt+msgid rows)

def overwriteInPo(tablePath, poPath, outPath = None):
	table = {}
	with open(tablePath, encoding = 'utf-8', newline = '') as f:
		for line in f:
			line = line.rstrip('\r\n')
			if not line:
				continue
			msgctxt, msgid, msgstr = line.split('\t')
			table[(msgctxt or None, msgid)] = msgstr

	po = polib.pofile(str(poPath))
	changed = 0
	for entry in po:
		key = (entry.msgctxt, entry.msgid)
		if key in table:
			entry.msgstr = table[key]
			changed += 1
	po.save(str(outPath or poPath))
	print(str(changed) + ' entries overwritten.')
