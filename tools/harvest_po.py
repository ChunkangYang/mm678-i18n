# Harvest translations for a language's .po from a LOCALIZED game install:
# extract the text files from the install's archives, align them row/column-
# wise with the English source via the template machinery, and fill the po.
#
#   python tools/harvest_po.py <lang> <game> <install-root>
#
# Run once per available game (mm6/mm7/mm8); the po must already exist
# (mm678 new-language <lang>). Files whose row count differs from the
# English source are skipped and reported (version drift) - positional
# alignment only, no guessing. When the same string is translated
# differently at different positions, the most frequent wins.
import collections
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import polib  # noqa: E402

from config.languages import LANGUAGES  # noqa: E402
from mm678i18n import pipeline  # noqa: E402
from mm678i18n.pipeline import (  # noqa: E402
	template2GlobalLineDict, source1stLang2MsgidList, canonicalizeMsgids,
	cleanStringList, compactPoFile, slashN2Lf)

CACHE = REPO / 'build' / 'media_extract'


def extractAll(arc, outDir):
	if not outDir.exists():
		outDir.mkdir(parents=True, exist_ok=True)
		r = subprocess.run([shutil.which('mmarch.cmd') or 'mmarch', 'extract',
			arc.name, str(outDir)], capture_output=True, text=True, cwd=str(arc.parent))
		if r.returncode != 0:
			print('  warning: mmarch failed on %s' % arc.name)
			return {}
	return {p.name.lower(): p for p in outDir.iterdir()}


# which archives may serve a file, by the family in its source path
# ('10LocLANG.<family>'): a broken same-named file in an unrelated archive
# (e.g. a junk MapStats.txt in the German ICONS.LOD) must not shadow the
# real one the game actually loads
FAMILY_MATCH = {
	'icons': lambda n: n.endswith('icons.lod'),
	'events': lambda n: n.endswith('events.lod'),
	'englisht': lambda n: n.endswith('t.lod') and not n.endswith('englishd.lod'),
	't': lambda n: n.endswith('t.lod') and not n.endswith('englishd.lod'),
}


def effectiveTexts(install, label):
	flat, byFam = {}, {fam: {} for fam in FAMILY_MATCH}
	for sub in install.iterdir():
		if sub.is_dir() and sub.name.lower() == 'data':
			for arc in sorted((p for p in sub.iterdir() if p.suffix.lower() == '.lod'),
					key=lambda p: p.name.lower()):
				files = extractAll(arc, CACHE / label / arc.name)
				flat.update(files)
				n = arc.name.lower()
				for fam, match in FAMILY_MATCH.items():
					if match(n):
						byFam[fam].update(files)
	# loose root files (mm*lang.ini etc.) win over nothing else
	for p in install.iterdir():
		if p.is_file() and p.suffix.lower() in ('.ini', '.txt', '.str'):
			flat.setdefault(p.name.lower(), p)
	return flat, byFam


def familyOf(filePath):
	for part in filePath.parts:
		low = part.lower()
		if low.startswith('10loclang.'):
			return low.split('.', 1)[1]
	return None


def main():
	if len(sys.argv) != 4:
		raise SystemExit('usage: python tools/harvest_po.py <lang> <game> <install-root>')
	lang, game, install = sys.argv[1], sys.argv[2], Path(sys.argv[3])
	enc = LANGUAGES[lang]['encoding']
	poPath = REPO / 'translations' / lang / 'LC_MESSAGES' / 'mm678.po'
	if not poPath.is_file():
		raise SystemExit('no po for %s - run: mm678 new-language %s' % (lang, lang))

	print('reading templates/EN source...')
	gld = template2GlobalLineDict()
	source1stLang2MsgidList(gld)
	canonicalizeMsgids(gld)

	print('extracting %s texts from %s...' % (game, install))
	# same cache label as tools/extract_media.py so archives extract once
	flat, byFam = effectiveTexts(install, '%s-%s' % (game, lang))

	harvest = collections.defaultdict(collections.Counter)

	def canon(s):
		return re.sub(r'(\\n|\s)+', ' ', s).strip()

	def poForm(s):
		# the pipeline escapes soft line breaks (\n) and double quotes (\")
		# as two-character sequences; po msgids round-trip through
		# dev-.py/gettext escaping into the REAL characters
		return slashN2Lf(s).replace('\\"', '"')

	def takeLine(ld, line, enLine, out):
		if 'msgidList' not in ld:
			return
		m = re.match(ld['regex'], line + '\r\n') or re.match(ld['regex'], line)
		if m:
			values = cleanStringList(list(m.groups()))
			for j, msgid in enumerate(ld['msgidList']):
				if j >= len(values):
					break
				msgstr = values[j]
				if msgstr:
					out.append((ld['msgctxtDict'].get(j), poForm(msgid), poForm(msgstr)))
			return
		# regex embeds the untranslated cells literally, so a cosmetic
		# difference there (e.g. the localized file drops the quotes around
		# a data cell) kills the whole line: fall back to tab-cell pairing
		# against the English source line
		if enLine is None or '\t' not in enLine:
			return
		enCells = cleanStringList(enLine.split('\t'))
		locCells = cleanStringList(line.split('\t'))
		used = set()
		for j, msgid in enumerate(ld['msgidList']):
			target = canon(msgid)
			for k, cell in enumerate(enCells):
				if k in used or k >= len(locCells):
					continue
				if canon(cell) == target:
					used.add(k)
					msgstr = locCells[k]
					if msgstr:
						out.append((ld['msgctxtDict'].get(j), poForm(msgid), poForm(msgstr)))
					break

	def commitFile(pairs):
		# a translation identical to the English is legitimate (Elf, Bonus,
		# NPC names...) as long as the file shows ANY localization at all -
		# a 100% identical file is an untouched English leftover and its
		# identical cells must not count as translations
		differing = sum(1 for _, mid, mstr in pairs if mstr != mid)
		takeIdentical = differing > 0
		for ctx, mid, mstr in pairs:
			if mstr != mid or takeIdentical:
				harvest[(ctx, mid)][mstr] += 1

	def uniqueKeys(lines):
		keys = [ln.split('\t', 1)[0].strip() for ln in lines]
		count = collections.Counter(keys)
		return {k: i for i, k in enumerate(keys) if k and count[k] == 1}

	skipped, missing, matchedFiles, keyAligned = [], [], 0, 0
	for filePath in gld:
		if filePath.parts[0] != game:
			continue
		fam = familyOf(filePath)
		locFile = None
		if fam in byFam:
			locFile = byFam[fam].get(filePath.name.lower())
		if locFile is None:
			locFile = flat.get(filePath.name.lower())
		if locFile is None:
			missing.append(filePath.name)
			continue
		text = locFile.read_bytes().decode(enc, errors='replace')
		locLines = text.split('\r\n')
		glen = len(gld[filePath])
		enPath = REPO / 'source' / 'en' / filePath
		enLines = enPath.read_bytes().decode('cp1252', errors='replace').split('\r\n') \
			if enPath.is_file() else []
		def enLine(i):
			return enLines[i] if i < len(enLines) else None
		# tolerate trailing empty-line padding
		while len(locLines) > glen and locLines[-1] == '':
			locLines.pop()
		if len(locLines) == glen:
			matchedFiles += 1
			pairs = []
			for i, line in enumerate(locLines):
				takeLine(gld[filePath][i], line, enLine(i), pairs)
			commitFile(pairs)
			continue
		# .str files: the game only ever APPENDED rows across versions
		# (verified: GrayFace 2.4/2.5.7 D-strs are identical prefixes), so
		# an older, shorter localized file aligns as a prefix - guarded by
		# the blank-row pattern having to match exactly
		if filePath.suffix.lower() == '.str' and len(locLines) < glen:
			n = len(locLines)
			enBlank = [not (enLines[i].strip() if i < len(enLines) else '') for i in range(n)]
			locBlank = [not locLines[i].strip() for i in range(n)]
			if enBlank == locBlank:
				pairs = []
				for i in range(n):
					takeLine(gld[filePath][i], locLines[i], enLine(i), pairs)
				commitFile(pairs)
				keyAligned += 1
				skipped.append('%s: prefix-aligned %d/%d rows'
					% (filePath.name, n, glen))
				continue
		# row drift: align .txt tables by their (unique) first-column key
		if filePath.suffix.lower() == '.txt' and enLines:
			enKeys = uniqueKeys(enLines[:glen])
			locKeys = uniqueKeys(locLines)
			common = set(enKeys) & set(locKeys)
			if len(common) >= max(3, glen // 4):
				pairs = []
				for k in common:
					takeLine(gld[filePath][enKeys[k]], locLines[locKeys[k]], enLine(enKeys[k]), pairs)
				commitFile(pairs)
				keyAligned += 1
				skipped.append('%s: key-aligned %d/%d rows (EN %d vs %s %d)'
					% (filePath.name, len(common), glen, glen, lang, len(locLines)))
				continue
		# last resort for any row drift: anchor alignment. Rows equal on
		# both sides (names, blanks, numbers) anchor the diff; a replaced
		# run of EQUAL length between anchors aligns positionally.
		if enLines:
			import difflib
			sm = difflib.SequenceMatcher(None, enLines[:glen], locLines, autojunk=False)
			pairs = []
			mapped = 0
			for tag, i1, i2, j1, j2 in sm.get_opcodes():
				if tag == 'equal' or (tag == 'replace' and (i2 - i1) == (j2 - j1)):
					for k in range(i2 - i1):
						takeLine(gld[filePath][i1 + k], locLines[j1 + k], enLine(i1 + k), pairs)
						mapped += 1
			if pairs:
				commitFile(pairs)
				keyAligned += 1
				skipped.append('%s: anchor-aligned %d/%d rows (EN %d vs %s %d)'
					% (filePath.name, mapped, glen, glen, lang, len(locLines)))
				continue
		skipped.append('%s (EN %d rows, %s %d rows)'
			% (filePath.name, glen, lang, len(locLines)))

	print('files: %d aligned, %d key-aligned, %d skipped/partial, %d not found'
		% (matchedFiles, keyAligned, len(skipped) - keyAligned, len(missing)))
	for s in skipped[:12]:
		print('  ', s)

	po = polib.pofile(str(poPath))
	filled = kept = 0
	for e in po:
		if e.obsolete or e.msgstr:
			kept += bool(e.msgstr)
			continue
		c = harvest.get((e.msgctxt, e.msgid))
		if c:
			e.msgstr = c.most_common(1)[0][0]
			filled += 1
	po.save(str(poPath))
	compactPoFile(poPath)
	total = sum(1 for e in po if not e.obsolete)
	trans = sum(1 for e in po if not e.obsolete and e.msgstr)
	print('%s: +%d filled from %s; now %d/%d translated'
		% (lang, filled, game, trans, total))
	rep = REPO / 'build' / ('harvest_%s_%s.txt' % (lang, game))
	rep.write_text('\n'.join(['SKIPPED ' + s for s in skipped]
		+ ['MISSING ' + m for m in missing]), encoding='utf-8')


main()
