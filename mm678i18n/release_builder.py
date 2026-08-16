# Release builder: postprod trees -> extract-over .zip archives (users
# unpack them over the game directory). Releases are PURE language packs;
# prerequisites (GrayFace patch, MMExtension) come from their official
# pages.
#
# Steps (`mm678 release` runs both):
#   1 compose   assemble each release working dir (files/)
#   2 zip       pack each files/ tree into the release .zip
#
# The release matrix lives in config/versions.py (`releases`).
# (The NSIS .exe installer chain and the bundled-extras trees were removed
# in 2026-08; see git history.)

import shutil
import zipfile
from pathlib import Path

from . import paths  # noqa: F401
from config import settings
from config.versions import releases, i18n_release


def copy_tree(src, dst):
	shutil.copytree(src, dst, dirs_exist_ok = True)


def buildPath():
	return Path(settings.release_build_folder)


def devDirOf(release):
	return buildPath().joinpath('dev').joinpath(release['lang']).joinpath(release['target'])


def compose():
	postprodPath = Path(settings.postprod_folder)
	for release in releases:
		devDir = devDirOf(release)
		devDir.mkdir(parents = True, exist_ok = True)
		filesDir = devDir.joinpath('files')
		if filesDir.is_dir():
			shutil.rmtree(filesDir)
		copy_tree(postprodPath.joinpath(release['lang']).joinpath(release['game']), filesDir)
		print('composed: ' + str(devDir))


# the archives contain exactly the files to lay over the game directory;
# *.todelete/*.mmarchkeep were installer-era marker files and are excluded
def makeZips():
	outDir = buildPath().joinpath('out')
	outDir.mkdir(parents = True, exist_ok = True)
	for release in releases:
		filesDir = devDirOf(release).joinpath('files')
		if not filesDir.is_dir():
			raise FileNotFoundError(str(filesDir) + " not found — run the 'compose' step first")
		zipPath = outDir.joinpath(release['outname'] + '_' + i18n_release['date'] + '.zip')
		with zipfile.ZipFile(zipPath, 'w', zipfile.ZIP_DEFLATED, compresslevel = 9) as zf:
			for p in sorted(filesDir.rglob('*')):
				if p.is_file() and p.suffix.lower() not in ['.todelete', '.mmarchkeep']:
					zf.write(p, p.relative_to(filesDir).as_posix())
		print('zipped: ' + str(zipPath))


STEPS = {
	'compose': compose,
	'zip': makeZips,
}


def run(steps = None):
	for name in (steps or list(STEPS)):
		STEPS[name]()
