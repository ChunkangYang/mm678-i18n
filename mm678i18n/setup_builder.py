# Installer builder: postprod trees + additional files -> NSIS setup .exe /
# extract-over .zip -> .7z
#
# Steps (all automated, `mm678 installers` runs them in order):
#   1 compose   assemble each installer working dir (files/, icon, script.nsi)
#   2 zip       pack each files/ tree into an extract-over-the-game-dir .zip
#   3 makensis  compile mm_i18n.nsi -> setup .exe   (requires NSIS)
#   4 collect   move the .exe files to the setup out dir, clean working files
#   5 compress  pack each .exe into a .7z            (requires 7-Zip)
#
# The installer matrix lives in config/versions.py (`installers`).

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

from . import paths  # noqa: F401
from .getfilepaths import getFilePaths
from config import settings
from config.versions import installers, i18n_release


def copy_tree(src, dst):
	shutil.copytree(src, dst, dirs_exist_ok = True)


def setupBuildPath():
	return Path(settings.setup_build_folder)


def devDirOf(installer):
	return setupBuildPath().joinpath('dev').joinpath(installer['lang']).joinpath(installer['target'])


def nsiSourceOf(installer):
	return Path(settings.installer_folder).joinpath('nsi').joinpath(installer['lang']).joinpath(installer['target']).joinpath('mm_i18n.nsi')


def findTool(envVar, names, defaultPaths, installHint):
	if os.environ.get(envVar):
		return os.environ[envVar]
	for name in names:
		found = shutil.which(name)
		if found:
			return found
	for p in defaultPaths:
		if Path(p).is_file():
			return p
	raise FileNotFoundError(
		'Cannot find ' + names[0] + '. ' + installHint +
		' (or set the ' + envVar + ' environment variable to its full path)')


def findMakensis():
	return findTool(
		'MAKENSIS', ['makensis'],
		[r'C:\Program Files (x86)\NSIS\makensis.exe', r'C:\Program Files\NSIS\makensis.exe'],
		'Install NSIS from https://nsis.sourceforge.io/')


def find7z():
	return findTool(
		'SEVENZIP', ['7z'],
		[r'C:\Program Files\7-Zip\7z.exe', r'C:\Program Files (x86)\7-Zip\7z.exe'],
		'Install 7-Zip from https://www.7-zip.org/')


def cleanDevDir(devDir):
	for name in ['files', 'mmarch.exe', 'script.nsi', 'icon.ico']:
		p = devDir.joinpath(name)
		if p.is_dir():
			shutil.rmtree(p)
		elif p.is_file():
			p.unlink()


# warn when the generated script.nsi no longer matches the FILE COPYING block
# of the hand-maintained mm_i18n.nsi (which is what actually gets compiled)
def warnOnNsiDrift(devDir, nsiSource = None):
	nsiPath = devDir.joinpath('mm_i18n.nsi')
	scriptPath = devDir.joinpath('script.nsi')
	if not (nsiPath.is_file() and scriptPath.is_file()):
		return
	nsiText = nsiPath.read_text(encoding = 'utf-8', errors = 'replace')
	startMark = ';-----FILE COPYING (MODIFYING, DELETING) STARTS HERE-----'
	endMark = ';-----FILE COPYING (MODIFYING, DELETING) ENDS HERE-----'
	if startMark not in nsiText or endMark not in nsiText:
		return
	fileOps = ('File ', 'Delete ', 'Rename ', 'RMDir', 'SetOutPath', 'CreateDirectory')
	def fileOpLines(text):
		return set(l.strip() for l in text.splitlines() if l.strip().startswith(fileOps))
	blockLines = fileOpLines(nsiText.split(startMark)[1].split(endMark)[0])
	scriptLines = fileOpLines(scriptPath.read_text(encoding = 'utf-8', errors = 'replace'))
	missing = scriptLines - blockLines
	extra = blockLines - scriptLines
	if missing or extra:
		print('WARNING: ' + str(nsiSource or nsiPath) + ' FILE COPYING block differs from generated script.nsi:')
		for l in sorted(missing):
			print('  only in script.nsi:  ' + l)
		for l in sorted(extra):
			print('  only in mm_i18n.nsi: ' + l)
		print('  -> review and update the block in mm_i18n.nsi if the change is intended.')


def compose():
	postprodPath = Path(settings.postprod_folder)
	additionalPath = Path(settings.installer_folder).joinpath('additional_files')
	for installer in installers:
		devDir = devDirOf(installer)
		devDir.mkdir(parents = True, exist_ok = True)
		cleanDevDir(devDir)

		shutil.copy(nsiSourceOf(installer), devDir.joinpath('mm_i18n.nsi'))
		shutil.copy(Path(settings.mmarch_exe), devDir.joinpath('mmarch.exe'))
		shutil.copy(additionalPath.joinpath('icons').joinpath(installer['icon']), devDir.joinpath('icon.ico'))

		filesDir = devDir.joinpath('files')
		for additional in installer['additional']:
			copy_tree(additionalPath.joinpath(additional), filesDir)
		copy_tree(postprodPath.joinpath(installer['lang']).joinpath(installer['game']), filesDir)

		subprocess.run(
			[str(devDir.joinpath('mmarch.exe').resolve()), 'df2n', str(filesDir), str(devDir.joinpath('script.nsi')), 'files'],
			check = True)
		warnOnNsiDrift(devDir, nsiSourceOf(installer))
		print('composed: ' + str(devDir))


# plain .zip alternative to the installer: users extract it over the game
# directory. Contains exactly the files the installer would copy (the
# *.todelete/*.mmarchkeep markers are excluded); unlike the installer it
# cannot delete obsolete files from very old patch versions.
def makeZips():
	outDir = setupBuildPath().joinpath('out')
	outDir.mkdir(parents = True, exist_ok = True)
	for installer in installers:
		filesDir = devDirOf(installer).joinpath('files')
		if not filesDir.is_dir():
			raise FileNotFoundError(str(filesDir) + " not found — run the 'compose' step first")
		zipPath = outDir.joinpath(installer['outname'] + '_Portable_' + i18n_release['date'] + '.zip')
		with zipfile.ZipFile(zipPath, 'w', zipfile.ZIP_DEFLATED, compresslevel = 9) as zf:
			for p in sorted(filesDir.rglob('*')):
				if p.is_file() and p.suffix.lower() not in ['.todelete', '.mmarchkeep']:
					zf.write(p, p.relative_to(filesDir).as_posix())
		print('zipped: ' + str(zipPath))


def makensis():
	makensisExe = findMakensis()
	for installer in installers:
		devDir = devDirOf(installer)
		subprocess.run(
			[makensisExe,
			 '/X' + 'SetCompressor /SOLID lzma',
			 '/DVERSION=' + i18n_release['date'],
			 '/DVERSIONDOT=' + i18n_release['dot'],
			 str(devDir.joinpath('mm_i18n.nsi'))],
			check = True)
		print('compiled: ' + str(devDir))


def collect():
	outDir = setupBuildPath().joinpath('out')
	outDir.mkdir(parents = True, exist_ok = True)
	for installer in installers:
		devDir = devDirOf(installer)
		cleanDevDir(devDir)
		for exe in getFilePaths(devDir, 'exe', False):
			shutil.move(str(exe), outDir.joinpath(exe.name))
			print('collected: ' + str(outDir.joinpath(exe.name)))


def compress():
	sevenZip = find7z()
	outDir = setupBuildPath().joinpath('out')
	for exe in getFilePaths(outDir, 'exe', False):
		archive = exe.with_suffix('.7z')
		subprocess.run(
			[sevenZip, 'a', '-t7z', str(archive), str(exe), '-m0=lzma2', '-mx=9', '-aoa'],
			check = True)
		exe.unlink()
		print('compressed: ' + str(archive))


STEPS = {
	'compose': compose,
	'zip': makeZips,
	'makensis': makensis,
	'collect': collect,
	'compress': compress,
}


def run(steps = None):
	for name in (steps or list(STEPS)):
		STEPS[name]()
