# Entry-level .po checks: placeholder integrity, control characters, and
# whitespace/newline drift. `mm678 check po` runs all of them; checks.py
# delegates its 'po' entry here.
#
# Placeholders come in two families that need different rules:
#   printf   %s %d %u %lu   filled positionally -> order is load-bearing
#   MM token %01-%34        each number is self-identifying -> order is free
# The patterns are an allowlist of the forms this project actually uses.
# A general printf grammar would mis-read literal '%' in prose ('100%
# behind', '10% chance per point of') as '% b' / '% c' / '% p'.

import collections
import hashlib
import re
import tomllib
from pathlib import Path

import polib

from config import settings

# numeric alternative first, so '%01' matches as one token rather than '%0'
TOKEN_RE = re.compile(r'%(?:[0-9]{1,2}|lu|[sdu])')

FAIL = 'FAIL'
WARN = 'WARN'
EXEMPT = 'EXEMPT'

Finding = collections.namedtuple('Finding', 'level check message detail')


def extractTokens(s):
	return TOKEN_RE.findall(s)


def isPrintf(tok):
	return not tok[1].isdigit()


def checkPlaceholders(msgid, msgstr):
	findings = []
	a, b = extractTokens(msgid), extractTokens(msgstr)
	if sorted(a) != sorted(b):
		findings.append(Finding(FAIL, 'placeholder-set',
			'placeholder set differs',
			'msgid ' + str(a) + ' -> msgstr ' + str(b)))
		return findings  # order is meaningless once the sets disagree
	pa = [t for t in a if isPrintf(t)]
	pb = [t for t in b if isPrintf(t)]
	if pa != pb:
		findings.append(Finding(FAIL, 'placeholder-order',
			'printf placeholders are filled positionally; reordering '
			'mismatches types',
			'msgid ' + str(pa) + ' -> msgstr ' + str(pb)))
	return findings


# All three are at zero occurrences repo-wide, so this is a canonicalisation
# rule rather than a corruption fix. TAB is the table field separator; CR
# would land inside a CRLF-delimited record; a literal backslash-n is turned
# into a real break by slashN2Lf at prod time, duplicating what a plain
# newline already does.
CONTROL_RULES = (
	('tab', '\t', 'msgstr contains a bare TAB (TAB is the table field separator)'),
	('cr', '\r', 'msgstr contains a CR'),
	('literal-slash-n', '\\n', 'msgstr contains a literal backslash-n; '
		'use a normal line break instead'),
)


def checkControlChars(msgstr):
	findings = []
	for check, needle, message in CONTROL_RULES:
		if needle in msgstr:
			findings.append(Finding(FAIL, check, message,
				'at offset ' + str(msgstr.index(needle))))
	return findings


# Layer 1 of the allowlist: the directional rule. A translation with LESS
# whitespace or FEWER line breaks than the source is exempt -- source
# trailing spaces are table padding and source breaks are English
# typesetting, so dropping them is correct. Additions are what get reported:
# trim_whitespace is false, so they reach the game verbatim.
#
# Count ' ' explicitly; bare strip() would also eat \n and \t, which have
# their own checks.

def leadingSpaces(s):
	return len(s) - len(s.lstrip(' '))


def trailingSpaces(s):
	return len(s) - len(s.rstrip(' '))


def checkWhitespace(msgid, msgstr):
	findings = []
	for label, count in (('leading', leadingSpaces), ('trailing', trailingSpaces)):
		a, b = count(msgid), count(msgstr)
		if b > a:
			findings.append(Finding(WARN, 'whitespace',
				'msgstr has ' + str(b - a) + ' extra ' + label + ' space(s)',
				'msgid ' + str(a) + ' -> msgstr ' + str(b)))
	return findings


def checkNewlines(msgid, msgstr):
	a, b = msgid.count('\n'), msgstr.count('\n')
	if b > a:
		return [Finding(WARN, 'newline',
			'msgstr has ' + str(b - a) + ' extra line break(s)',
			'msgid ' + str(a) + ' -> msgstr ' + str(b))]
	return []


# The mirror image of the two functions above: what the directional rule
# silently allows. Only --show-exempt asks for these.
def exemptDifferences(msgid, msgstr):
	findings = []
	for label, count in (('leading', leadingSpaces), ('trailing', trailingSpaces)):
		a, b = count(msgid), count(msgstr)
		if b < a:
			findings.append(Finding(EXEMPT, 'whitespace',
				'msgstr drops ' + str(a - b) + ' ' + label + ' space(s)',
				'msgid ' + str(a) + ' -> msgstr ' + str(b)))
	a, b = msgid.count('\n'), msgstr.count('\n')
	if b < a:
		findings.append(Finding(EXEMPT, 'newline',
			'msgstr drops ' + str(a - b) + ' line break(s)',
			'msgid ' + str(a) + ' -> msgstr ' + str(b)))
	return findings


# ---- allowlist (layer 2: per-entry exemptions) ----
# msgctxt alone is not unique -- it holds semantic tags like 'location' and
# 'npcprof' shared across thousands of entries -- so the key hashes the
# gettext identity pair. Hashing survives .po re-sorting and line shifts.

ALLOWLIST_PATH = Path(__file__).resolve().parent.parent / 'config' / 'po_allowlist.toml'


def entryKey(msgctxt, msgid):
	raw = (msgctxt or '') + '\x04' + msgid
	return hashlib.sha1(raw.encode('UTF-8')).hexdigest()[:12]


def loadAllowlist(path = None):
	p = Path(path) if path is not None else ALLOWLIST_PATH
	if not p.is_file():
		return {}
	with p.open('rb') as f:
		data = tomllib.load(f)
	allowlist = {}
	for row in data.get('allow', []):
		k = (row['lang'], row['key'])
		allowlist.setdefault(k, set()).update(row.get('checks', []))
	return allowlist


def isAllowed(allowlist, lang, key, check):
	return check in allowlist.get((lang, key), ())


# ---- aggregation ----

def checkEntry(entry, lang, allowlist, showExempt = False):
	if entry.obsolete or 'fuzzy' in entry.flags or not entry.msgstr:
		return []
	key = entryKey(entry.msgctxt, entry.msgid)
	findings = (checkPlaceholders(entry.msgid, entry.msgstr)
		+ checkControlChars(entry.msgstr)
		+ checkWhitespace(entry.msgid, entry.msgstr)
		+ checkNewlines(entry.msgid, entry.msgstr))
	kept = [f for f in findings if not isAllowed(allowlist, lang, key, f.check)]
	# EXEMPT findings are informational, so the allowlist does not apply
	return kept + (exemptDifferences(entry.msgid, entry.msgstr) if showExempt else [])


def checkFile(path, lang, allowlist, strict = False, showExempt = False):
	po = polib.pofile(str(path))
	pairs = []
	for entry in po:
		for f in checkEntry(entry, lang, allowlist, showExempt):
			if strict and f.level == WARN:
				f = f._replace(level = FAIL)
			pairs.append((entry, f))
	return pairs, len(po), po.percent_translated()


def formatFinding(path, entry, finding):
	return ('%s %s:%s  %s\n'
		'       msgid  %r\n'
		'       msgstr %r\n'
		'       %s (%s)' % (finding.level, path, entry.linenum, finding.check,
			entry.msgid[:70], entry.msgstr[:70], finding.message, finding.detail))


def run(langs = None, strict = False, showExempt = False, printKey = None):
	i18nPath = Path(settings.i18n_folder)
	allowlist = loadAllowlist()
	fails = warns = 0
	for p in sorted(i18nPath.glob('*/' + settings.textdomain + '.po')):
		lang = p.parent.name
		if langs and lang not in langs:
			continue
		if printKey and lang != printKey:
			continue
		try:
			pairs, total, percent = checkFile(p, lang, allowlist, strict, showExempt)
		except Exception as e:          # the 'parse' check
			fails += 1
			print('FAIL ' + str(p) + ': ' + str(e))
			continue
		if printKey:
			for entry, f in pairs:
				if f.level == EXEMPT:
					continue
				print('%s  %-16s %s' % (entryKey(entry.msgctxt, entry.msgid),
					f.check, entry.msgid[:60].replace('\n', ' ')))
			continue
		if not pairs:
			print('OK   %s  (%d entries, %s%% translated)' % (p, total, percent))
		for entry, f in pairs:
			if f.level == FAIL:
				fails += 1
			elif f.level == WARN:
				warns += 1
			print(formatFinding(p, entry, f))
	if not printKey:
		print('%d problem(s), %d warning(s).' % (fails, warns))
	return fails
