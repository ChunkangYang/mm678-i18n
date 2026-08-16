# Sync source/en with the text files of upstream game installs.
#
#   python tools/upstream_sync.py fingerprint <game> <install> [<install2> ...]
#       Byte-compare our tracked source/en/<game> files against each install
#       (archives are extracted to build/upstream_extract). Identifies the
#       baseline and the upstream change volume.
#
#   python tools/upstream_sync.py pull <game> <install>
#       Overwrite source/en/<game> with the install's current files (tracked
#       file set only - brand-new upstream files are not auto-added).
#       Review with `git diff source/en` afterwards.
#
# Mapping: a source subfolder named 10LocLANG.<tag> corresponds to the
# install's Data\<tag>.lod; root-level source files are loose files in the
# install root. mmmerge's "Data/Text localization" + "nonprod" files come
# from Rodril's translation template (not from the install) and
# Data/LocalizeConf.ini is our own file - those are skipped and listed.
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / 'source' / 'en'


def gameFiles(game):
	base = SRC / game
	buckets = {'archive': {}, 'root': [], 'special': []}
	for p in sorted(base.rglob('*')):
		if not p.is_file():
			continue
		rel = p.relative_to(base)
		parts = rel.parts
		if len(parts) == 1:
			buckets['root'].append(rel)
		elif any(x.startswith('10LocLANG.') for x in parts):
			tag = next(x for x in parts if x.startswith('10LocLANG.'))[len('10LocLANG.'):]
			buckets['archive'].setdefault(tag, []).append(rel)
		else:
			buckets['special'].append(rel)
	return base, buckets


def archivePath(install, tag):
	for cand in (Path(install) / 'Data' / (tag + '.lod'),
	             Path(install) / 'DATA' / (tag + '.lod')):
		if cand.exists():
			return cand
	raise SystemExit('archive not found in install: %s.lod (%s)' % (tag, install))


# newer MM Merge builds moved the scroll/dialog .STR files out of
# EnglishT.lod into the per-continent text archive mmmerge.T.lod
FALLBACK_ARCHIVES = {'mmmerge': ['mmmerge.T.lod']}


def extractInto(arc, outDir, names):
	outDir.mkdir(parents = True, exist_ok = True)
	r = subprocess.run(['mmarch.cmd', 'extract', arc.name, str(outDir)] + names,
		capture_output = True, text = True, cwd = str(arc.parent))
	if r.returncode != 0:
		raise SystemExit('mmarch extract failed: ' + (r.stderr or r.stdout)[:300])
	return {p.name.lower(): p for p in outDir.iterdir()}


def collect(install, game, buckets, label):
	# returns {rel: bytes or None} for every tracked file
	got = {}
	for tag, rels in buckets['archive'].items():
		arc = archivePath(install, tag)
		outDir = REPO / 'build' / 'upstream_extract' / label / game / tag
		byLower = extractInto(arc, outDir, [rel.name for rel in rels])
		for rel in rels:
			p = byLower.get(rel.name.lower())
			got[rel] = p.read_bytes() if p else None
		for fbName in FALLBACK_ARCHIVES.get(game, []):
			pending = [rel for rel in rels if got[rel] is None]
			if not pending:
				break
			fbArc = arc.parent / fbName
			if not fbArc.exists():
				continue
			listed = subprocess.run(['mmarch.cmd', 'list', fbArc.name],
				capture_output = True, text = True, cwd = str(fbArc.parent))
			inFb = {n.strip().lower() for n in listed.stdout.splitlines()}
			names = [rel.name for rel in pending if rel.name.lower() in inFb]
			if not names:
				continue
			fbOut = REPO / 'build' / 'upstream_extract' / label / game / fbName
			byLower = extractInto(fbArc, fbOut, names)
			for rel in pending:
				p = byLower.get(rel.name.lower())
				if p:
					got[rel] = p.read_bytes()
	for rel in buckets['root']:
		p = Path(install) / rel.name
		got[rel] = p.read_bytes() if p.exists() else None
	return got


def fingerprint(game, installs):
	base, buckets = gameFiles(game)
	for install in installs:
		label = Path(install).name
		got = collect(install, game, buckets, 'fp_' + label)
		same = changed = missing = 0
		for rel, data in got.items():
			if data is None:
				missing += 1
			elif data == (base / rel).read_bytes():
				same += 1
			else:
				changed += 1
		print('%-42s %s: %d same, %d changed, %d missing (of %d)'
			% (label, game, same, changed, missing, len(got)))
	if buckets['special']:
		print('  (skipped %d template/own files)' % len(buckets['special']))


def pull(game, install):
	base, buckets = gameFiles(game)
	got = collect(install, game, buckets, 'pull')
	changed = 0
	for rel, data in sorted(got.items()):
		if data is None:
			print('MISSING upstream (kept ours): ' + rel.as_posix())
			continue
		dst = base / rel
		if data != dst.read_bytes():
			changed += 1
			print('  updated: ' + rel.as_posix())
		dst.write_bytes(data)
	print('%s: %d of %d tracked files updated' % (game, changed, len(got)))
	if buckets['special']:
		print('NOT pulled (translation-template / our own files):')
		for r in buckets['special']:
			print('  ' + r.as_posix())


def rowKey(line):
	return line.split(b'\t', 1)[0]


def keyedRows(data):
	d = {}
	for line in data.split(b'\r\n'):
		k = rowKey(line)
		if k and k not in d:
			d[k] = line
	return d


def mergeTableRows(ours, old, new):
	# new file's structure/order wins; a row is swapped back to ours only when
	# WE changed it and upstream did not. Returns (merged, keptOurs, trueConf)
	ro, ru = keyedRows(old), keyedRows(ours)
	keptOurs, trueConf = [], []
	outLines = []
	seen = set()
	for line in new.split(b'\r\n'):
		k = rowKey(line)
		if k and k not in seen:
			seen.add(k)
			o, u = ro.get(k), ru.get(k)
			if o is not None and u is not None and u != o:
				if line == o: # upstream untouched: our edit survives
					outLines.append(u)
					keptOurs.append(k)
					continue
				if line != u: # three-way distinct: upstream wins, log it
					trueConf.append(k)
		outLines.append(line)
	return b'\r\n'.join(outLines), keptOurs, trueConf


def sync3(game, oldInstall, newInstall, write):
	# three-way: our source vs the old baseline install vs the latest install.
	#   upstream changed + we never edited  -> pull latest
	#   upstream unchanged (incl. our deliberate edits) -> keep ours
	#   both changed -> CONFLICT, keep ours, list for manual re-application
	base, buckets = gameFiles(game)
	old = collect(oldInstall, game, buckets, 'old')
	new = collect(newInstall, game, buckets, 'new')
	pulled, merged, ourEdits = [], [], []
	for rel in sorted(old, key = lambda r: r.as_posix()):
		o, n = old[rel], new[rel]
		ours = (base / rel).read_bytes()
		upstreamChanged = (o is not None and n is not None and o != n) \
			or (o is None and n is not None and n != ours)
		weEdited = o is not None and ours != o
		if weEdited:
			ourEdits.append(rel.as_posix())
		if upstreamChanged and not weEdited:
			pulled.append(rel.as_posix())
			if write:
				(base / rel).write_bytes(n)
		elif upstreamChanged and weEdited:
			# row-level three-way merge (upstream structure wins; rows only
			# we edited survive; three-way-distinct rows go upstream + log)
			out, keptOurs, trueConf = mergeTableRows(ours, o, n)
			merged.append((rel.as_posix(), keptOurs, trueConf))
			if write:
				(base / rel).write_bytes(out)
	print('== %s: %d clean pulls, %d row-merged, %d files with our edits'
		% (game, len(pulled), len(merged), len(ourEdits)))
	for x in pulled:
		print('  pulled: ' + x)
	for name, keptOurs, trueConf in merged:
		print('  merged: %s (kept %d of our rows; %d rows went upstream: %s%s)'
			% (name, len(keptOurs), len(trueConf),
			   b','.join(trueConf[:10]).decode('cp1252', 'replace'),
			   '...' if len(trueConf) > 10 else ''))


if __name__ == '__main__':
	mode, game = sys.argv[1], sys.argv[2]
	if mode == 'fingerprint':
		fingerprint(game, sys.argv[3:])
	elif mode == 'pull':
		pull(game, sys.argv[3])
	elif mode in ('sync3', 'sync3-dry'):
		sync3(game, sys.argv[3], sys.argv[4], mode == 'sync3')
	else:
		raise SystemExit('unknown mode: ' + mode)
