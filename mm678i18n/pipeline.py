# Text pipeline core (formerly csv2po.py v1.0.0)
# By Tom CHEN <tomchen.org@gmail.com> (tomchen.org)
# MIT License
#
# source (game text files) + template  ->  dev (.py with gettext calls)
#                                      ->  pot/po (translation files)
# po -> mo -> prod (translated game text files)
#
# Paths are repo-root-relative; run with the repo root as working directory
# (the CLI does this automatically).

import re
import glob
import os
import time
import importlib.util
import gettext
import polib
from pathlib import Path

from . import paths  # noqa: F401 (makes `config` importable)
from .pluralforms import pluralforms
from config import settings

__version__ = '1.0.0'

# ========== Settings init START ==========

def setDefaults(defaultsDict):
	for key in defaultsDict:
		if not hasattr(settings, key) or getattr(settings, key) == '':
			setattr(settings, key, defaultsDict[key])

setDefaults({
	'project_name'              : 'My Project',
	'author_name'               : 'John Doe',
	'author_email'              : 'johndoe@example.com',
	'team_name'                 : 'My Team',

	'source_folder'             : 'source',
	'template_folder'           : 'build/templates_ctx',
	'dev_folder'                : 'build/dev',
	'i18n_folder'               : 'translations',
	'prod_folder'               : 'build/prod',

	'file_extensions'           : ['txt'],

	'template_repl'             : '_(TRANS)_',
	'template_repl_with_context': '_(TRANS_CONTEXT:<context>)_',
	'template_encoding'         : 'UTF-8',

	'first_language'            : 'en',
	'source_encoding'           : {},
	'encoding_errors_handling'  : 'ignore',

	'i18n_language_exclusion'   : [],
	'prod_language_exclusion'   : [],

	'separator'                 : '\t',
	'eol'                       : '\n',
	'lf_in_crlf_mode'           : False,

	'trim_whitespace'           : False,
	'trim_doublequote'          : True,
	'trim_singlequote'          : False,
	'convert_two_quotes_to_one' : True,

	'no_log'                    : True,
	'no_warning'                : False
})


# lang lists (global variables)
# - sourceLangs/langs: languages with a source folder (normally just the
#   first language now: the .po files are the only store of translations)
# - i18nDirLangs/prodLangs: languages with a .po in the i18n folder
#   (drive the mo/prod phases; first language builds from msgids directly)
sourceLangs = list(map(lambda x: x.name, list(Path(settings.source_folder).glob('*'))))

cleanedI18nLangExcl = settings.i18n_language_exclusion
cleanedI18nLangExcl = [x for x in cleanedI18nLangExcl if x != settings.first_language] # cleanedI18nLangExcl can't have first language
setattr(settings, 'i18n_language_exclusion', cleanedI18nLangExcl)

langs = [x for x in sourceLangs if x not in cleanedI18nLangExcl] # i18n langs

i18nDirLangs = sorted([x.name for x in Path(settings.i18n_folder).glob('*') if x.is_dir()])

prodLangs = [x for x in [settings.first_language] + i18nDirLangs if x not in settings.prod_language_exclusion] # prod langs


# defaults for settings.source_encoding[lang]
for lang in set(langs) | set(prodLangs):
	if lang not in settings.source_encoding or settings.source_encoding[lang] == '':
		settings.source_encoding[lang] = 'UTF-8' # set default


# lf_in_crlf_mode is effective only when eol = '\r\n'
if settings.lf_in_crlf_mode and settings.eol != '\r\n':
	setattr(settings, 'lf_in_crlf_mode', False)


# ========== Settings init END ==========


# ========== Utility functions START ==========

def log(s, error = 'w'):
	if error == 'w':
		printHead = 'Warning: '
	elif error == 'e':
		printHead = 'Error: '
	elif error == 'n':
		printHead = 'Note: '
	if settings.no_log == False:
		f = Path('logfile.txt').open(mode = 'a+', newline = '\n', encoding = 'UTF-8')
		f.write(printHead + s + '\n')
		f.close()
	if error == 'e':
		raise ValueError(printHead + s)
	elif settings.no_warning == False:
		print(printHead + s)


def getFilePaths(pathObj, extension = 'txt', recursive = True):
	if recursive:
		pathPre = '**/'
	else:
		pathPre = ''
	if type(extension) is list:
		retList = []
		for thisExt in extension:
			retList += getFilePaths(pathObj, extension = thisExt, recursive = recursive)
		return retList
	else:
		return list(pathObj.glob(pathPre + '*.' + extension))

# ========== Utility functions END ==========


# ========== Functions START ==========

def encodingFix(s, encoding, decode = True):
	if encoding.lower() == 'gb2312':
		if decode: # read
			return s.replace(u'\u30FB', u'\u00B7').replace(u'\u2015', u'\u2014')
		else:
			return s.replace(u'\u00B7', u'\u30FB').replace(u'\u2014', u'\u2015').replace(u'\u2013', u'\u2015')
	return s

# use all files in /<template>/ to generate globalLineDict[filePath]
def template2GlobalLineDict():
	globalLineDict = {}
	for filePathComplete in getFilePaths(Path(settings.template_folder), settings.file_extensions):
		f = filePathComplete.open(mode = 'r', newline = settings.eol, encoding = settings.template_encoding, errors = settings.encoding_errors_handling)
		filePath = filePathComplete.relative_to(settings.template_folder)
		globalLineDict[filePath] = []
		for line in f:
			line = encodingFix(line, settings.template_encoding)
			lineMatches = re.findall('(' + re.escape(settings.template_repl) + ')|' + re.escape(settings.template_repl_with_context).replace('<context>', '(.*?)'), line)
			lineSplitList = re.compile(re.escape(settings.template_repl) + '|' + re.escape(settings.template_repl_with_context).replace('<context>', '.*?')).split(line)
			transCount = len(lineMatches)
			msgctxtDict = {}
			for i, tu in enumerate(lineMatches):
				if tu[0] == '':
					msgctxtDict[i] = tu[1]
			regex = ''
			lslLen = len(lineSplitList)
			if lslLen > 1:
				for i in range(lslLen - 1):
					regex += re.escape(lineSplitList[i])
					if settings.eol != '\r\n':
						regex += '([^' + settings.separator + '^' + settings.eol + ']*)'
					else:
						regex += '((?:[^' + settings.separator + '^\r]|\r(?!\n))*)'
				lslLastMatchObj = re.match('(.*?)(?:\t|\r\n)', lineSplitList[lslLen - 1])
				if lslLastMatchObj != None:
					regex += re.escape(lslLastMatchObj.group(1))
			globalLineDict[filePath].append({
				'transCount': transCount,
				'regex': regex,
				'lineSplitList': lineSplitList.copy(),
				'msgctxtDict': msgctxtDict.copy(),
			})
	return globalLineDict


# convert LF ('\n') (non CRLF ('\r\n')) in a string to `Slash N` ('\\n')
def lf2SlashN(s):
	return re.sub('(?<!\r)\n', r'\\n', s)

# convert `Slash N` ('\\n') back to LF ('\n') [don't care about CRLF]
def slashN2Lf(s):
	return re.sub(r'\\n', '\n', s)

def escapeTab(s):
	return re.sub('\t', r'\\t', s)

def sanitizeDoubleQuote(s):
	return s.replace('"', r'\"')

def cleanString(s):
	if settings.trim_whitespace:
		s = s.strip()
	if settings.trim_doublequote:
		s = re.sub('^"|"$', '', s)
		if settings.convert_two_quotes_to_one:
			s = s.replace('""', '"')
	if settings.trim_singlequote:
		s = re.sub('^\'|\'$', '', s)
		if settings.convert_two_quotes_to_one:
			s = s.replace('\'\'', '\'')
	if settings.lf_in_crlf_mode:
		s = lf2SlashN(s)
	s = sanitizeDoubleQuote(s)
	return s

def cleanStringList(l):
	return list(map(lambda s: cleanString(s), l))


# use globalLineDict[filePath] to match all files in /<source>/<first_language>/ to get msgidList in globalLineDict[filePath]
def source1stLang2MsgidList(globalLineDict):
	for filePath in globalLineDict:
		p0 = Path(settings.source_folder).joinpath(settings.first_language).joinpath(filePath)
		if p0.is_file():
			f0 = p0.open(mode = 'r', newline = settings.eol, encoding = settings.source_encoding[settings.first_language], errors = settings.encoding_errors_handling)
			for i, line in enumerate(f0):
				line = encodingFix(line, settings.source_encoding[settings.first_language])
				lineDict = globalLineDict[filePath][i]
				matchObj = re.match(lineDict['regex'], line)
				if matchObj:
					msgidList = matchObj.groups()
					msgidList = cleanStringList(msgidList)
					lineDict['msgidList'] = msgidList
					for msgid in lineDict['msgidList']:
						if msgid == '':
							log('At least one of msgids in line ' + str(i + 1) + ' in first-language file ' + str(p0) + ' is an empty string. It may cause problem in later process.')
				else:
					log('Line ' + str(i + 1) + ' in first-language file ' + str(p0) + ' doesn\'t correspond to its template. First language file must be well present and correspond to the template file.', 'e')
			f0.close()
		else:
			log('Can\'t find first-language file ' + str(p0) + '. First language file must be well present and correspond to the template file.', 'e')

# collapse whitespace-variant twins of the same string into ONE msgid per
# context: upstream sources write the same text both "sentence.  Next" (the
# classic games) and "sentence.\nNext" (the Merge translation template), which
# would otherwise duplicate entries. The canonical form is the first one seen
# in walk order (mm6/mm7/mm8 before mmmerge), keeping historical msgids - and
# translations - stable.
def canonicalizeMsgids(globalLineDict):
	canon = {}
	# when the same string appears in several games in cosmetically
	# different forms, the NEWEST game's form becomes the canonical msgid
	# (mmmerge > mm8 > mm7 > mm6)
	gamePriority = {'mmmerge': 0, 'mm8': 1, 'mm7': 2, 'mm6': 3}
	for filePath in sorted(globalLineDict,
			key = lambda p: (gamePriority.get(p.parts[0], 9), str(p).lower())):
		for lineDict in globalLineDict[filePath]:
			if 'msgidList' not in lineDict:
				continue
			msgidList = list(lineDict['msgidList'])
			for i, msgid in enumerate(msgidList):
				ctx = lineDict['msgctxtDict'].get(i)
				key = (ctx, re.sub(r'(\\n|\s)+', ' ', msgid).strip())
				msgidList[i] = canon.setdefault(key, msgid)
			lineDict['msgidList'] = msgidList


# use globalLineDict[filePath] to generate all files in /<dev>/
def source1stLang2Dev(globalLineDict):
	for filePath in globalLineDict:
		p = Path(settings.dev_folder).joinpath(filePath)
		p = p.with_suffix(p.suffix + '.py')
		p.parent.mkdir(parents = True, exist_ok = True)
		fDev = p.open(mode = 'w', newline = '\n', encoding = 'UTF-8')
		fDev.write('def t(_, _x):\n\tr = []\n')
		for lineDict in globalLineDict[filePath]:
			lem1 = len(lineDict['lineSplitList']) - 1
			splitListStr = ''
			for j in range(lem1): # lem1 could be 0 in which case the following `for` block is skipped
				if j in lineDict['msgctxtDict']:
					splitListStr += repr(lineDict['lineSplitList'][j]) + ' + _x("' + lineDict['msgctxtDict'][j] + '", "' + (lineDict['msgidList'][j]) + '") + '
				else:
					splitListStr += repr(lineDict['lineSplitList'][j]) + ' + _("' + (lineDict['msgidList'][j]) + '") + '
			splitListStr += repr(lineDict['lineSplitList'][lem1])
			# one append statement per template line: a single giant expression
			# would exceed CPython's fixed compiler recursion limit (3.12+)
			fDev.write('\tr.append(' + splitListStr + ')\n')
		fDev.write('\treturn "".join(r)\n')
		fDev.close()


# use globalLineDict[filePath] to match all files in /<source>/<first_language>/ to generate potDict without msgstr
def globalLineDict2PotDict(globalLineDict):
	potDict = {}
	for filePath in globalLineDict:
		for lineIndex, lineDict in enumerate(globalLineDict[filePath]):
			if 'msgidList' in lineDict:
				for i, msgid in enumerate(lineDict['msgidList']):
					if i in lineDict['msgctxtDict']:
						msgctxt = lineDict['msgctxtDict'][i]
					else:
						msgctxt = None
					msgTuple = (msgid, msgctxt)
					if msgTuple in potDict:
						loc = potDict[(msgid, msgctxt)]['locations']
						pathLineTuple = (filePath.with_suffix(filePath.suffix + '.py'), lineIndex + 1)
						if pathLineTuple not in loc:
							loc.append(pathLineTuple)
					else:
						potDict[(msgid, msgctxt)] = {
							'locations': [
								(filePath.with_suffix(filePath.suffix + '.py'), lineIndex + 1)
							]
						}
	return potDict


# get a language's plural form. Plural form is like 'nplurals=2; plural=(n != 1);', 'nplurals=1; plural=0;', etc.
# uses pluralforms.py. If not in the dict, returns None
def getPluralForm(lang):
	if lang in pluralforms:
		return pluralforms[lang]
	else:
		return pluralforms.get(lang.split('_')[0], None)


# write via a temp file + atomic replace, retrying on transient locks
# (AV/editor holds intermittently EINVAL direct 'w' opens on po files here,
# which truncates the target before failing)
def writeFileAtomic(path, text, encoding = 'UTF-8'):
	path = Path(path)
	tmp = path.with_name(path.name + '.tmp')
	with tmp.open(mode = 'w', newline = '\n', encoding = encoding) as f:
		f.write(text)
	for attempt in range(8):
		try:
			os.replace(tmp, path)
			return
		except OSError:
			if attempt == 7:
				raise
			time.sleep(0.7)


# gettext-style greedy wrap of "#:" reference comments at ~78 columns
def wrapRefs(refs):
	lines = []
	cur = '#:'
	for r in refs:
		if cur != '#:' and len(cur) + 1 + len(r) > 78:
			lines.append(cur)
			cur = '#:'
		cur += ' ' + r
	lines.append(cur)
	return '\n'.join(lines) + '\n'


# use potDict to generate first language's .pot or non-first language's .po file
# .pot, .po files are ALWAYS encoded in UTF-8 with LF as EOL
def generatePoFile(potDict, isPot = True, lang = settings.first_language):
	p = Path(settings.i18n_folder)
	if not isPot:
		p = p.joinpath(lang)
	p = p.joinpath(settings.textdomain + ('.pot' if isPot else '.po'))
	p.parent.mkdir(parents = True, exist_ok = True)

	pluralform = getPluralForm(lang)
	currentTime = time.strftime("%Y-%m-%d %H:%M%z", time.localtime())

	lineStr = '''#, fuzzy
''' if isPot else ''

	lineStr += '''msgid ""
msgstr ""
"Project-Id-Version: ''' + settings.project_name + '''\\n"
"POT-Creation-Date: ''' + currentTime + '''\\n"
"PO-Revision-Date: ''' + currentTime + '''\\n"
"Last-Translator: ''' + settings.author_name + ''' <''' + settings.author_email + '''>\\n"
"Language-Team: ''' + settings.team_name + '''\\n"
"Language: ''' + lang + '''\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"X-Generator: CSV2PO Python Script ''' + __version__ + '''\\n"
"X-Poedit-Basepath: ''' + Path(os.path.relpath(settings.dev_folder, p.parent)).as_posix() + '''\\n"
''' + ('"Plural-Forms: ' + pluralform + '''\\n"
''' if pluralform != None else '') + '''"X-Poedit-SourceCharset: UTF-8\\n"
"X-Poedit-KeywordsList: pgettext:1c,2;_x:1c,2\\n"
"X-Poedit-SearchPath-0: .\\n"

'''
	for msgTuple in potDict:
		msgInfo = potDict[msgTuple]
		locMap = map(lambda tu: tu[0].as_posix() + ':' + str(tu[1]), msgInfo['locations'])
		lineStr += wrapRefs(locMap)
		if msgTuple[1] != None:
			lineStr += 'msgctxt "' + msgTuple[1] + '"\n'
		lineStr += 'msgid "' + msgTuple[0] + '"\n'
		# print(msgInfo)
		if not isPot and 'msgstr' in msgInfo and lang in msgInfo['msgstr']:
			msgstr = msgInfo['msgstr'][lang]
		else:
			msgstr = ''
		lineStr += 'msgstr "' + msgstr + '"\n'
		lineStr += '\n'
	writeFileAtomic(p, lineStr)


# The legacy full-extraction machinery (getWordList/addCustomList/
# findMsgstr/conflict_priority and the `bootstrap` command) that harvested
# msgstrs from pre-translated game files in source/<lang> was removed after
# the 2026-08 upgrade: the .po files are the single store of translations
# now. See git history and references/notes/zh (archived override lists)
# if a future language ever needs a seeded start - a targeted harvest
# script in tools/ is the better shape for that anyway.



def discoveredLangs():
	return sorted(x.name for x in Path(settings.i18n_folder).glob('*') if x.is_dir())


# regenerate the derived languages' .po from their source language
# (config/languages.py DERIVED_LANGUAGES, e.g. zh_TW from zh_CN via OpenCC)
def deriveLanguages():
	from config.languages import DERIVED_LANGUAGES
	from . import zhconvert
	for target, (srcLang, method) in DERIVED_LANGUAGES.items():
		zhconvert.run(method = method, sourceLang = srcLang, targetLang = target)


# compile all .po to .mo files (derived languages regenerated first)
def po2Mo(langs = None):
	deriveLanguages()
	for currentLang in discoveredLangs():
		if langs and currentLang not in langs:
			continue
		p = Path(settings.i18n_folder).joinpath(currentLang).joinpath(settings.textdomain + '.po')
		if not p.is_file():
			log('No .po file for language ' + currentLang + ' (' + str(p) + '), skipped.')
			continue
		polib.pofile(str(p)).save_as_mofile(str(p.with_suffix('.mo')))


# rewrite a .po/.pot with every msgid/msgstr on a single line (no gettext
# line-splitting at \n, no width wrapping) - purely presentational, the
# string content is identical
def compactPoFile(path):
	import re as _re
	text = Path(path).read_text(encoding = 'utf-8')
	# the header entry (empty msgid at the top) keeps its conventional
	# one-metadata-field-per-line format; expand it if it was compacted
	sep = text.find('\n\n')
	head, tail = (text[:sep + 1], text[sep + 1:]) if sep > 0 else ('', text)
	m = _re.search(r'^msgstr "(.+)"\n', head, _re.M)
	if m and '\\n' in m.group(1):
		fields = ''.join('"%s\\n"\n' % p for p in m.group(1).split('\\n') if p != '')
		head = head[:m.start()] + 'msgstr ""\n' + fields + head[m.end():]
	# rewrap "#:" reference comments treating each "path:line" as atomic:
	# polib breaks at any space, splitting paths like "Text localization"
	refPattern = _re.compile(r'^((?:#: [^\n]*\n)+)', _re.M)
	def rewrap(mm):
		joined = ' '.join(ln[3:] for ln in mm.group(1).rstrip('\n').split('\n'))
		refs = [r.strip() for r in _re.findall(r'.+?:\d+(?= |$)', joined)]
		return wrapRefs(refs)
	tail = refPattern.sub(rewrap, tail)
	pattern = _re.compile(
		r'^((?:#~ )?msg(?:id|str|ctxt|id_plural)(?:\[\d+\])?) ""\n((?:(?:#~ )?"[^\n]*"\n)+)',
		_re.M)
	def join(mm):
		key, block = mm.group(1), mm.group(2)
		obsolete = key.startswith('#~ ')
		parts = []
		for line in block.rstrip('\n').split('\n'):
			if obsolete and line.startswith('#~ '):
				line = line[3:]
			parts.append(line[1:-1]) # strip the surrounding quotes
		joined = ''.join(parts)
		if joined == '': # a genuinely empty string keeps the "" form
			return key + ' ""\n'
		return key + ' "' + joined + '"\n'
	writeFileAtomic(path, head + pattern.sub(join, tail), encoding = 'utf-8')


# non-destructive .po update after template/source changes: regenerate dev
# and a fresh .pot, then merge every existing .po against it. Translations
# are preserved; new strings appear untranslated, removed ones go obsolete.
# GNU msgmerge is used when on PATH (adds fuzzy matching for changed
# strings); the polib merge otherwise. Derived languages are skipped (they
# are regenerated from their source language at build time).
def updatePo():
	import shutil
	import subprocess
	from config.languages import DERIVED_LANGUAGES
	from . import context

	# regenerate the with-context templates from scratch: batchAddContext
	# only ever adds files, so a stale build/templates_ctx would silently
	# feed removed templates (or, if wiped externally, nothing at all)
	ctxPath = Path(settings.template_folder)
	if ctxPath.is_dir():
		shutil.rmtree(ctxPath)
	context.run()

	globalLineDict = template2GlobalLineDict()
	source1stLang2MsgidList(globalLineDict)
	canonicalizeMsgids(globalLineDict)
	source1stLang2Dev(globalLineDict)
	potDict = globalLineDict2PotDict(globalLineDict)
	generatePoFile(potDict)
	potPath = Path(settings.i18n_folder).joinpath(settings.textdomain + '.pot')
	msgmerge = shutil.which('msgmerge')
	for currentLang in discoveredLangs():
		if currentLang in DERIVED_LANGUAGES:
			continue
		poPath = Path(settings.i18n_folder).joinpath(currentLang, settings.textdomain + '.po')
		if not poPath.is_file():
			continue
		if msgmerge:
			subprocess.run([msgmerge, '--update', '--backup=off', '--no-wrap',
				str(poPath), str(potPath)], check = True)
		else:
			po = polib.pofile(str(poPath))
			po.merge(polib.pofile(str(potPath)))
			tmp = str(poPath) + '.tmp'
			po.save(tmp)
			for attempt in range(8):
				try:
					os.replace(tmp, str(poPath))
					break
				except OSError:
					if attempt == 7:
						raise
					time.sleep(0.7)
		compactPoFile(poPath)
		total = translated = 0
		for e in polib.pofile(str(poPath)):
			if e.obsolete:
				continue
			total += 1
			if e.msgstr:
				translated += 1
		print('updated %s: %d entries, %d translated, %d untranslated'
			% (poPath, total, translated, total - translated))

# get dev text functions from all dev modules
def getDevTextDict():
	import sys
	sys.dont_write_bytecode = True # keep __pycache__ out of the dev folder
	devTextDict = {}
	for p in getFilePaths(Path(settings.dev_folder), 'py'):
		filePath = p.relative_to(settings.dev_folder).with_suffix('')
		spec = importlib.util.spec_from_file_location(p.name, p)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		devTextDict[filePath] = module.t
	return devTextDict

# generate prod files for a single language
# untranslated strings fall back to the English source text, which can hold
# characters the target game encoding cannot express (e.g. 'ï' in gb2312):
# transliterate those to their base ASCII instead of failing the build
def _translitError(e):
	import unicodedata
	out = []
	for ch in e.object[e.start:e.end]:
		d = unicodedata.normalize('NFKD', ch).encode('ascii', 'ignore').decode()
		out.append(d or '?')
	return (''.join(out), e.end)


import codecs
codecs.register_error('mm678translit', _translitError)


def generateProdForLang(lang, devTextDict):
	# load the .mo directly from translations/<lang>/ (we do not use the
	# GNU <lang>/LC_MESSAGES/<domain>.mo convention gettext.translation()
	# would insist on)
	moPath = Path.cwd().joinpath(settings.i18n_folder, lang, settings.textdomain + '.mo')
	if moPath.is_file():
		with moPath.open('rb') as f:
			trans = gettext.GNUTranslations(f)
	else:
		trans = gettext.NullTranslations()

	def _(message):
		ret = trans.gettext(message)
		if settings.lf_in_crlf_mode:
			ret = slashN2Lf(ret)
		ret = escapeTab(ret)
		return ret

	def _x(context, message):
		ret = trans.pgettext(context, message)
		if settings.lf_in_crlf_mode:
			ret = slashN2Lf(ret)
		ret = escapeTab(ret)
		return ret

	for path in devTextDict:
		devText = devTextDict[path]
		p = Path(settings.prod_folder).joinpath(lang).joinpath(path)
		p.parent.mkdir(parents = True, exist_ok = True)
		f = p.open(mode = 'w', newline = '', encoding = settings.source_encoding[lang], errors = 'mm678translit')
		f.write(encodingFix(devText(_, _x), settings.source_encoding[lang], False))
		f.close()

# generate prod files for all languages
def generateProdForAllLang(langs, devTextDict):
	for lang in langs:
		generateProdForLang(lang, devTextDict)

# generate prod files from .mo files
def mo2Prod(langs):
	devTextDict = getDevTextDict()
	generateProdForAllLang(langs, devTextDict)


# ========== Functions END ==========



# ========== Procedural START ==========

def generateDevOnly():
	globalLineDict = template2GlobalLineDict()
	source1stLang2MsgidList(globalLineDict)
	canonicalizeMsgids(globalLineDict)
	source1stLang2Dev(globalLineDict)



def generateProd(onlyLangs = None):
	# build/ is disposable: after a deleted build tree (or a fresh checkout)
	# build/dev is gone, and an empty dev would silently produce an empty
	# prod — regenerate templates + dev first
	if not any(Path(settings.dev_folder).rglob('*.py')):
		print('build/dev is missing — regenerating it (templates + dev) first')
		from . import context
		context.run()
		generateDevOnly()
	# clean output first: prod only ever overwrites, so files whose template
	# was removed would otherwise linger and leak into postprod. With a
	# language filter, clean only the filtered languages' trees.
	import shutil
	prodPath = Path(settings.prod_folder)
	if prodPath.exists():
		if onlyLangs:
			for lang in onlyLangs:
				p = prodPath.joinpath(lang)
				if p.exists():
					shutil.rmtree(p)
		else:
			shutil.rmtree(prodPath)
	# recompute instead of using the import-time snapshot: derived languages
	# (e.g. zh_TW) may have been created by po2Mo within the same run
	langs = [x for x in dict.fromkeys([settings.first_language] + discoveredLangs())
		if x not in settings.prod_language_exclusion]
	if onlyLangs:
		langs = [x for x in langs if x in onlyLangs]
	mo2Prod(langs)



# create the .po for ONE new language without touching any other language.
# All msgstr are left empty: translation happens in Poedit from there
def newLanguage(lang):
	if lang == settings.first_language:
		log('Language ' + lang + ' is the first (source) language; it needs no .po file.', 'e')
	if lang not in settings.source_encoding or settings.source_encoding[lang] == '':
		settings.source_encoding[lang] = 'UTF-8'

	globalLineDict = template2GlobalLineDict()
	source1stLang2MsgidList(globalLineDict)
	canonicalizeMsgids(globalLineDict)
	potDict = globalLineDict2PotDict(globalLineDict)
	generatePoFile(potDict, False, lang)
	log('Created ' + settings.i18n_folder + '/' + lang + '/' + settings.textdomain + '.po', 'n')


# ========== Procedural END ==========


# potDict = {
# 	('msgid', 'msgctxt'): { # 'msgctxt' could be None or ''
# 		'locations': [
# 			(Path1, 21), # Path line tuple
# 			(Path2, 34)
# 		],
# 		'msgstr': {
# 			'zh_CN': '??',
# 			'fr': '??'
# 		}
# 	},
# 	...
# }

# globalLineDict = {
# 	'filePath': [
# 		{ # each line
# 			'transCount': 2,
# 			'regex': r'',
# 			'lineSplitList': ['23'],
# 			'msgctxtDict': {0: 'abbr for category'},
# 			'msgidList': ['cat', 'dog']
# 		},
# 		...
# 	]
# }
