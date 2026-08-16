# Reclaim translations for entries whose msgid differs from an already
# translated twin only cosmetically. Two passes:
#   1. strict: whitespace-normalized match (collapse all \s runs)
#   2. loose:  additionally ignore trailing periods/spaces (upstream typo
#      class like "we find.." vs "we find.")
# Same-context matches are preferred; cross-context matches are taken when
# every candidate agrees on the translation. msgids are NOT merged - only
# msgstr is copied (the sources genuinely differ, e.g. an upstream typo).
#
#   python tools/recover_po.py [po-path]
import re
import sys
from pathlib import Path

import polib

REPO = Path(__file__).resolve().parent.parent
PO = Path(sys.argv[1]) if len(sys.argv) > 1 else \
	REPO / 'translations' / 'zh_CN' / 'LC_MESSAGES' / 'mm678.po'


# when an untranslated entry's context is the key, translations from the
# listed contexts may be taken even if other-context candidates disagree
# (e.g. Global.txt stat rows historically carried an explicit 'stats' ctx)
CTX_FALLBACK = {'global': ['stats', 'spells']}


def normWs(s):
	return re.sub(r'\s+', ' ', s).strip()


_QUOTES = str.maketrans({'‘': "'", '’': "'", '“': '"', '”': '"'})


def normLoose(s):
	# additionally fold quote styles (upstream mixes straight and curly) and
	# ignore trailing periods (typo class "we find..")
	return normWs(s).translate(_QUOTES).rstrip('. ')


def normNoWs(s):
	# whitespace removed entirely: catches the template's glued sentence
	# joins ("darkness.Both") against the games' spaced/newlined forms
	return re.sub(r'(\\n|\s)+', '', s).translate(_QUOTES).rstrip('. ')


def editDist(a, b):
	if abs(len(a) - len(b)) > 2:
		return 3
	prev = list(range(len(b) + 1))
	for i, ca in enumerate(a):
		cur = [i + 1]
		for j, cb in enumerate(b):
			cur.append(min(prev[j + 1] + 1, cur[j] + 1, prev[j] + (ca != cb)))
		prev = cur
	return prev[-1]


def typoEquivalent(a, b):
	# same word count and every differing word is a small typo/case fix
	# (edit distance <= 2, no digit changes) - excludes semantic swaps like
	# Light <-> Dark (distance 4)
	wa, wb = normLoose(a).split(' '), normLoose(b).split(' ')
	if len(wa) != len(wb):
		return False
	for x, y in zip(wa, wb):
		if x == y:
			continue
		if any(ch.isdigit() for ch in x + y):
			return False
		if editDist(x.lower(), y.lower()) > 2:
			return False
	return True


po = polib.pofile(str(PO))
index = {'ws': {}, 'loose': {}, 'nospace': {}, 'nocase': {}}
for e in po:
	# obsolete entries included: retired whitespace twins still carry
	# reclaimable translations
	if not e.msgstr:
		continue
	index['ws'].setdefault(normWs(e.msgid), []).append(e)
	index['loose'].setdefault(normLoose(e.msgid), []).append(e)
	index['nospace'].setdefault(normNoWs(e.msgid), []).append(e)
	index['nocase'].setdefault(normNoWs(e.msgid).lower(), []).append(e)

stats = {'ws': 0, 'loose': 0, 'nospace': 0, 'nocase': 0, 'ambiguous': 0}
report = []
for e in po:
	if e.obsolete or e.msgstr:
		continue
	for mode, normf in (('ws', normWs), ('loose', normLoose), ('nospace', normNoWs),
			('nocase', lambda s: normNoWs(s).lower())):
		cands = index[mode].get(normf(e.msgid))
		if not cands:
			continue
		sameCtx = [c for c in cands if c.msgctxt == e.msgctxt]
		pick = None
		if sameCtx:
			pick = sameCtx[0]
		if pick is None: # fallback contexts, in listed preference order
			for fb in CTX_FALLBACK.get(e.msgctxt, []):
				lst = [c for c in cands if c.msgctxt == fb]
				if lst:
					pick = lst[0]
					break
		if pick is None and len({c.msgstr for c in cands}) == 1:
			pick = cands[0]
		if pick is None:
			stats['ambiguous'] += 1
			report.append('AMBIGUOUS [%s] %s' % (e.msgctxt, e.msgid[:70].replace('\n', ' ')))
			break
		e.msgstr = pick.msgstr
		stats[mode] += 1
		report.append('%s [%s] <- [%s] %s' % (mode, e.msgctxt, pick.msgctxt,
			e.msgid[:70].replace('\n', ' ')))
		break

# pass 3: typo-level matches among what's still untranslated. Candidates are
# found by similarity, then gated by the strict word-by-word typo test.
import difflib
transList = [(normLoose(e.msgid), e) for e in po if e.msgstr]
transKeys = [k for k, _ in transList]
transBy = {}
for k, e in transList:
	transBy.setdefault(k, e)
stats['typo'] = 0
for e in po:
	if e.obsolete or e.msgstr:
		continue
	n = normLoose(e.msgid)
	for close in difflib.get_close_matches(n, transKeys, n = 3, cutoff = 0.9):
		cand = transBy[close]
		if typoEquivalent(e.msgid, cand.msgid):
			e.msgstr = cand.msgstr
			stats['typo'] += 1
			report.append('typo [%s] <- [%s] %s || %s' % (e.msgctxt, cand.msgctxt,
				e.msgid[:60].replace('\n', ' '), cand.msgid[:60].replace('\n', ' ')))
			break

po.save(str(PO))
sys.path.insert(0, str(REPO))
from mm678i18n.pipeline import compactPoFile  # noqa: E402
compactPoFile(PO)

total = sum(1 for e in po if not e.obsolete)
translated = sum(1 for e in po if not e.obsolete and e.msgstr)
print('recovered: %d whitespace, %d loose-punct, %d no-space, %d case-only, %d typo-level, %d ambiguous skipped'
	% (stats['ws'], stats['loose'], stats['nospace'], stats['nocase'], stats['typo'], stats['ambiguous']))
print('now: %d entries, %d translated, %d untranslated'
	% (total, translated, total - translated))
(REPO / 'build' / 'recover_po_report.txt').write_text('\n'.join(report), encoding = 'utf-8')
print('report: build/recover_po_report.txt')
