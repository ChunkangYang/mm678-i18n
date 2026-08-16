# Regenerate the per-language translation glossaries from the .po files.
#
#   references/glossary/glossary-terms.tsv   curated, language-neutral term
#                                            selection (msgctxt <TAB> English)
#   references/glossary/<lang>/glossary.tsv  generated: context, English, and
#                                            the language's CURRENT po
#                                            translation
#
# The po is the single store of translations, so glossary translations are
# always looked up there at build time - a glossary can never go stale.
# Derived languages (zh_TW) get no glossary: they convert automatically.
#
#   python tools/build_glossary.py [lang ...]     default: all languages
#                                                 with a translated po
import re
import sys
from pathlib import Path

import polib

REPO = Path(__file__).resolve().parent.parent
TERMS = REPO / 'references' / 'glossary' / 'glossary-terms.tsv'

sys.path.insert(0, str(REPO))
from config.languages import DERIVED_LANGUAGES  # noqa: E402


def normWs(s):
	return re.sub(r'(\\n|\s)+', ' ', s).strip()


def loadTerms():
	terms = []
	for ln in TERMS.read_text(encoding = 'utf-8').splitlines():
		if not ln.strip() or ln.startswith('#'):
			continue
		ctx, en = ln.split('\t', 1)
		terms.append((ctx.strip(), en.strip()))
	return terms


def buildIndexes(po):
	exact, norm, byEn, byLower = {}, {}, {}, {}
	for e in po:
		if not e.msgstr:
			continue
		# obsolete entries included: a term retired upstream still has its
		# last known translation there
		key = (e.msgctxt, e.msgid)
		if e.obsolete:
			exact.setdefault(key, e.msgstr)
			norm.setdefault((e.msgctxt, normWs(e.msgid)), e.msgstr)
		else:
			exact[key] = e.msgstr
			norm[(e.msgctxt, normWs(e.msgid))] = e.msgstr
		byEn.setdefault(normWs(e.msgid), set()).add((e.msgid, e.msgstr))
		byLower.setdefault(normWs(e.msgid).lower(), set()).add((e.msgid, e.msgstr))
	return exact, norm, byEn, byLower


def buildFor(lang, report):
	poPath = REPO / 'translations' / lang / 'LC_MESSAGES' / 'mm678.po'
	po = polib.pofile(str(poPath))
	if not any(e.msgstr for e in po if not e.obsolete):
		print('%s: po has no translations, skipped' % lang)
		return
	exact, norm, byEn, byLower = buildIndexes(po)

	outDir = REPO / 'references' / 'glossary' / lang
	outDir.mkdir(parents = True, exist_ok = True)
	rows, missing = [], 0
	for ctx, en in loadTerms():
		tr = exact.get((ctx, en))
		if tr is None:
			tr = norm.get((ctx, normWs(en)))
		if tr is None: # any context, but only when unambiguous
			cands = byEn.get(normWs(en), set())
			if len(cands) == 1:
				tr = next(iter(cands))[1]
		if tr is None: # case drift: take the po's live casing for English too
			cands = byLower.get(normWs(en).lower(), set())
			if len(cands) == 1:
				en, tr = next(iter(cands))
		if tr is None:
			tr = ''
			missing += 1
			report.append('%s MISSING [%s] %s' % (lang, ctx, en))
		rows.append('%s\t%s\t%s' % (ctx, en, tr))

	head = [
		'# GENERATED - do not edit translations here. Regenerate with:',
		'#   python tools/build_glossary.py',
		'# Term selection lives in references/glossary/glossary-terms.tsv;',
		'# the translations are looked up in translations/%s/.../mm678.po.' % lang,
		'# Columns: msgctxt <TAB> English <TAB> %s' % lang,
	]
	out = outDir / 'glossary.tsv'
	out.write_text('\n'.join(head + rows) + '\n', encoding = 'utf-8', newline = '\n')
	print('%s: %d terms -> %s (%d without translation)'
		% (lang, len(rows), out.relative_to(REPO), missing))


langs = sys.argv[1:]
if not langs:
	langs = sorted(x.name for x in (REPO / 'translations').glob('*')
		if x.is_dir() and x.name not in DERIVED_LANGUAGES)
report = []
for lang in langs:
	buildFor(lang, report)
(REPO / 'build' / 'glossary_report.txt').write_text(
	'\n'.join(report) + '\n', encoding = 'utf-8')
if report:
	print('%d terms lack a po translation: build/glossary_report.txt' % len(report))
