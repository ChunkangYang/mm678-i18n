# Extract localizable media (images / dub audio / video) from a localized
# (non-English) game install into assets/*/prod/<lang>/<game>, by byte-
# comparing every archive entry against the ENGLISH install so only files
# the localizers actually changed are taken (no dead weight).
#
#   python tools/extract_media.py <lang> <game> <loc-install> <en-install>
#          [--sound] [--video] [--all-images]
#
#   lang         target language code, e.g. ja, ko, fr
#   game         mm6 | mm7 | mm8 | mmmerge
#   loc-install  root of the localized game installation
#   en-install   root of the clean English installation of the same game
#                (use C:\game\mm\mmoriglang\* / original-latest as reference)
#
# Images: entries with an image extension that differ from English AND whose
# filename is in the reference set (what zh_CN localizes, per
# docs/dev/media.md) are copied into the standard assets layout; differing
# images OUTSIDE the reference set are only reported (candidates for human
# review; --all-images copies them too, into a folder named after their
# archive family). Sound (--sound) and video (--video) take every differing
# entry (dubs are wholesale replacements).
#
# Archives are loaded name-sorted with last-wins, mirroring the game.
# Extraction cache: build/media_extract/<label>/ (safe to delete).
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CACHE = REPO / 'build' / 'media_extract'

IMG_EXT = {'.bmp', '.pcx', '.tga', '.act'}
SND_EXT = {'.wav'}
VID_EXT = {'.smk', '.bik'}

# family (the part of the archive name after the first dot) -> assets dir
# name used when an out-of-reference candidate is copied with --all-images
FAMILY_DIR = {
	'icons.lod': 'icons', 'events.lod': 'events', 'englisht.lod': 'EnglishT',
	'englishd.lod': 'EnglishD', 'd.lod': 'EnglishD', 't.lod': 'EnglishT',
	'bitmaps.lod': 'bitmaps', 'sprites.lod': 'sprites', 'games.lod': 'games',
	'new.lod': 'icons',
}


def fail(msg):
	raise SystemExit('error: ' + msg)


def extractAll(arc, outDir):
	if not outDir.exists():
		outDir.mkdir(parents=True, exist_ok=True)
		r = subprocess.run([shutil.which('mmarch.cmd') or 'mmarch', 'extract',
			arc.name, str(outDir)], capture_output=True, text=True, cwd=str(arc.parent))
		if r.returncode != 0:
			print('  warning: mmarch failed on %s (%s)' % (arc.name, (r.stderr or r.stdout)[:120].strip()))
			return {}
	return {p.name.lower(): p for p in outDir.iterdir()}


def effective(install, label, subdir, suffixes):
	# name-sorted last-wins across every matching archive in <install>/<subdir>
	root = None
	for cand in install.iterdir():
		if cand.is_dir() and cand.name.lower() == subdir:
			root = cand
			break
	if root is None:
		return {}, {}
	eff, fam = {}, {}
	for arc in sorted((p for p in root.iterdir()
			if p.suffix.lower().lstrip('.') in suffixes), key=lambda p: p.name.lower()):
		# 'icons.lod' and '00 patch.icons.lod' are the same family: the
		# last two dot-separated parts of the name
		family = '.'.join(arc.name.lower().split('.')[-2:])
		for n, p in extractAll(arc, CACHE / label / arc.name).items():
			eff[n] = p
			fam[n] = family
	return eff, fam


def referenceLayout(game):
	# where does zh_CN put each localized image? -> {filename: relative dir}
	layout = {}
	roots = [REPO / 'assets' / 'img' / 'prod' / 'zh_CN' / game]
	if game in ('mm8', 'mmmerge'):
		roots.append(REPO / 'assets' / 'img' / 'prod' / 'zh_CN' / 'mmmerge_and_mm8')
	for root in roots:
		if not root.exists():
			continue
		for p in root.rglob('*'):
			if p.is_file():
				layout[p.name.lower()] = p.parent.relative_to(root)
	return layout


def main():
	args = [a for a in sys.argv[1:] if not a.startswith('--')]
	flags = {a for a in sys.argv[1:] if a.startswith('--')}
	if len(args) != 4:
		fail(__doc__ or 'see header for usage')
	lang, game, locRoot, enRoot = args[0], args[1], Path(args[2]), Path(args[3])
	if game not in ('mm6', 'mm7', 'mm8', 'mmmerge'):
		fail('game must be mm6/mm7/mm8/mmmerge')
	for p in (locRoot, enRoot):
		if not p.is_dir():
			fail('not a directory: %s' % p)

	ref = referenceLayout(game)
	report = []

	# ---- images (data/*.lod) ----
	locEff, locFam = effective(locRoot, '%s-%s' % (game, lang), 'data', {'lod'})
	enEff, _ = effective(enRoot, '%s-en' % game, 'data', {'lod'})
	outImgRoot = REPO / 'assets' / 'img' / 'prod' / lang / game
	copied = candidates = 0
	for n, p in sorted(locEff.items()):
		if Path(n).suffix.lower() not in IMG_EXT:
			continue
		e = enEff.get(n)
		if e is not None and p.read_bytes() == e.read_bytes():
			continue  # identical to English: not a localization
		if n in ref:
			dest = outImgRoot / ref[n] / p.name
			dest.parent.mkdir(parents=True, exist_ok=True)
			shutil.copy2(p, dest)
			copied += 1
		elif '--all-images' in flags:
			dest = outImgRoot / 'Data' / FAMILY_DIR.get(locFam[n], 'icons') / p.name
			dest.parent.mkdir(parents=True, exist_ok=True)
			shutil.copy2(p, dest)
			copied += 1
		else:
			candidates += 1
			report.append('CANDIDATE %s (%s)%s' % (n, locFam[n],
				'' if e is not None else ' [not in EN]'))
	print('images: %d copied into %s, %d out-of-reference candidates'
		% (copied, outImgRoot.relative_to(REPO), candidates))

	# ---- dub audio (sounds/*.snd) ----
	if '--sound' in flags:
		locS, _ = effective(locRoot, '%s-%s-snd' % (game, lang), 'sounds', {'snd'})
		enS, _ = effective(enRoot, '%s-en-snd' % game, 'sounds', {'snd'})
		outSnd = REPO / 'assets' / 'sound' / 'prod' / lang / game / 'Sounds' / 'Audio'
		nS = 0
		for n, p in sorted(locS.items()):
			e = enS.get(n)
			if e is not None and p.read_bytes() == e.read_bytes():
				continue
			outSnd.mkdir(parents=True, exist_ok=True)
			shutil.copy2(p, outSnd / p.name)
			nS += 1
		print('sound: %d differing entries -> %s' % (nS, outSnd.relative_to(REPO)))

	# ---- video (anims/*.vid archives + loose smk/bik) ----
	if '--video' in flags:
		locV, locVFam = effective(locRoot, '%s-%s-vid' % (game, lang), 'anims', {'vid'})
		enV, _ = effective(enRoot, '%s-en-vid' % game, 'anims', {'vid'})
		for root, m in ((locRoot, locV), (enRoot, enV)):
			for cand in root.iterdir():
				if cand.is_dir() and cand.name.lower() == 'anims':
					for p in cand.iterdir():
						if p.suffix.lower() in VID_EXT:
							m.setdefault(p.name.lower(), p)
		outVid = REPO / 'assets' / 'video' / 'prod' / lang / game / 'Anims'
		nV = 0
		for n, p in sorted(locV.items()):
			if Path(n).suffix.lower() not in VID_EXT:
				continue
			e = enV.get(n)
			if e is not None and p.read_bytes() == e.read_bytes():
				continue
			sub = locVFam.get(n, '').split('.')[0]
			dest = outVid / sub / p.name if sub else outVid / p.name
			dest.parent.mkdir(parents=True, exist_ok=True)
			shutil.copy2(p, dest)
			nV += 1
		print('video: %d differing entries -> %s' % (nV, outVid.relative_to(REPO)))

	repPath = REPO / 'build' / ('media_extract_%s_%s.txt' % (game, lang))
	repPath.write_text('\n'.join(report) + '\n', encoding='utf-8')
	if report:
		print('review the out-of-reference candidates: %s' % repPath.relative_to(REPO))


main()
