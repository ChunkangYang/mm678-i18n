# Postprod: prod (translated text) + non-text assets -> installable file trees
# per language/game (DBCS special encoding, fonts, scripts, images, archives).

import configparser
import re
import shutil
import subprocess
from pathlib import Path

from . import paths  # noqa: F401
from .getfilepaths import getFilePaths
from .dbcs_special import encodeDbcsSpecialFile
from config import settings
from config.languages import LANGUAGES, langEncDict, dbcsLangs, dbcsEncs
from config.versions import versions


def copy_tree(src, dst):
	shutil.copytree(src, dst, dirs_exist_ok = True)


# Documented BDF font-mapping template appended to LocalizeConf.ini of
# native-renderer builds (configparser cannot round-trip comments, so this is
# written as raw text after the managed keys); the empty values are filled
# from the language's dbcs_fonts map (config/languages.py). Heights/styles
# were measured from the shipped engine fonts and are identical across MM6/7/8.
DBCS_FONT_TEMPLATE = '''
[dbcsFont]
; BDF font mapping (native DBCS renderer, FNT_DBCS.lua). Each line maps an
; engine font to a .bdf file in Data\\DBCSFonts\\; an empty value falls back
; to Default. Glyph placement is automatic: blank rows a BDF pads its glyphs
; with are cropped away and the glyph sits one pixel below the game font's
; baseline. An integer flag (0-10) adds that many pixels of line spacing for
; THIS font only (e.g. Smallnum=font.bdf,2; stacks with lineSpacing above).
; The glyph style (shadow / plain / black) is auto-detected from each game
; font's own glyphs; add a shadow/plain/black flag only to override it.
; Default takes one or more comma-separated files; fonts without their own
; line pick from them by height (largest that fits, else smallest).
Default=
; Lucida: height 17, shadow style
Lucida=
; Smallnum: height 14, shadow style (smallest UI font)
Smallnum=
; Arrus: height 19, shadow style (main dialog font)
Arrus=
; Create: height 18, shadow style (character creation)
Create=
; Comic: height 19, shadow style
Comic=
; Book: height 25, shadow style (book headings)
Book=
; Book2: height 30, shadow style (large titles)
Book2=
; Cchar: height 29, shadow style (credits; MM6/MM7)
Cchar=
; Autonote: height 18, black style
Autonote=
; Spell: height 16, plain style (no shadow)
Spell=
'''


def mmarch(*args):
	# resolve through PATH (npm installs a .cmd shim, which plain
	# subprocess.run would not find without shutil.which)
	exe = shutil.which(settings.mmarch_exe) or settings.mmarch_exe
	subprocess.run([str(exe)] + list(args), check = True)


def copyFonts(d, pTemp, mmVersion, pNameCondensed):
	if mmVersion == '6':
		targetLod = 'icons'
	elif mmVersion == '7':
		targetLod = 'events'
	else: # 8 or merge
		targetLod = 'EnglishT'
	fontDir = Path(settings.non_text_folder).joinpath('font').joinpath(d)
	if not fontDir.exists(): # e.g. DBCS encodings: BDFs replaced the page .fnt
		return
	for fnt in getFilePaths(fontDir, 'fnt', False):
		shutil.copy(fnt, pTemp.joinpath('Data/10 Loc' + pNameCondensed + '.' + targetLod))


def rewriteProgramName(pIni, enc):
	# store program_name in UTF-8: ProgramName.lua detects that (strict UTF-8
	# validation), converts to the user's SYSTEM codepage for the engine's
	# ANSI buffer and sets the window title in real Unicode. cp1250/cp1251
	# names keep the legacy raw-bytes format (no runtime converter for them).
	if enc not in dbcsEncs and enc != 'cp1252':
		return
	out = []
	for line in pIni.read_bytes().split(b'\r\n'):
		if line.startswith(b'program_name='):
			name = line[len(b'program_name='):].decode(enc)
			out.append(b'program_name=' + name.encode('utf-8'))
		else:
			out.append(line)
	pIni.write_bytes(b'\r\n'.join(out))


def stripBdf(raw, keepCps):
	# drop the glyphs of code points the language's encoding can never
	# request (the renderer resolves glyphs through the encoding's .tbl, so
	# this is lossless for it) - smaller files load and scan much faster
	end = raw.find(b'\nENDFONT')
	tail = raw[end + 1:] if end >= 0 else b'ENDFONT\n'
	body = raw[:end + 1] if end >= 0 else raw
	parts = body.split(b'STARTCHAR')
	kept = []
	for part in parts[1:]:
		m = re.search(rb'\nENCODING (\d+)', part)
		if m and int(m.group(1)) in keepCps:
			kept.append(b'STARTCHAR' + part)
	head = re.sub(rb'\nCHARS \d+\n', b'\nCHARS %d\n' % len(kept), parts[0], count = 1)
	return head + b''.join(kept) + tail


def tblCodepoints(pTbl):
	data = pTbl.read_bytes()
	cps = set()
	for i in range(0, len(data) - 1, 2):
		cp = data[i] | (data[i + 1] << 8)
		if cp:
			cps.add(cp)
	return cps


_strippedBdfCache = {}

def copyDbcsFonts(langName, pTemp):
	# the language's BDF fonts (stripped to its charset) + the encoding's
	# Unicode table (<enc>.tbl), loaded by FNT_DBCS.lua from Data\DBCSFonts\
	# (plain folder, not a LOD)
	fonts = LANGUAGES[langName].get('dbcs_fonts')
	if not fonts:
		return
	dst = pTemp.joinpath('Data/DBCSFonts')
	dst.mkdir(parents = True, exist_ok = True)
	src = Path(settings.non_text_folder).joinpath('font')
	enc = langEncDict[langName]
	shutil.copy(src.joinpath(enc + '.tbl'), dst.joinpath(enc + '.tbl'))
	keep = None
	for name in sorted({value.split(',')[0] for value in fonts.values()}):
		key = (name, enc)
		if key not in _strippedBdfCache:
			if keep is None:
				keep = tblCodepoints(src.joinpath(enc + '.tbl'))
			_strippedBdfCache[key] = stripBdf(src.joinpath(name).read_bytes(), keep)
		dst.joinpath(name).write_bytes(_strippedBdfCache[key])


def processProdText(postprodPath, prodPath):
	if postprodPath.exists():
		shutil.rmtree(postprodPath)

	for p in getFilePaths(prodPath, '', True):
		if p.name == 'nonprod' and p.exists():
			shutil.rmtree(p)

	for p in getFilePaths(prodPath, '', False):
		if p.name in dbcsLangs:
			# per game: native-renderer games ship plain DBCS text, the rest
			# keep the legacy marker encoding (see settings.native_dbcs_games)
			for game in getFilePaths(p, '', False):
				dest = postprodPath.joinpath(p.name).joinpath(game.name)
				if not game.is_dir():
					dest.parent.mkdir(parents = True, exist_ok = True)
					shutil.copy(game, dest)
				elif game.name in settings.native_dbcs_games:
					shutil.copytree(game, dest)
				else:
					encodeDbcsSpecialFile(game, dest, langEncDict[p.name])
		else:
			shutil.copytree(p, postprodPath.joinpath(p.name))

	for p in getFilePaths(postprodPath, '', False):
		pNameCondensed = p.name.upper().replace('_', '') # e.g. ZHCN

		pTemp = p.joinpath('mm6/data/10LocLANG.icons')
		if pTemp.exists():
			pTemp.rename(pTemp.parent.joinpath('10 Loc' + pNameCondensed + '.icons'))

		pTemp = p.joinpath('mm7/DATA/10LocLANG.events')
		if pTemp.exists():
			pTemp.rename(pTemp.parent.joinpath('10 Loc' + pNameCondensed + '.events'))

		pTemp = p.joinpath('mm8/Data/10LocLANG.EnglishT')
		if pTemp.exists():
			pTemp.rename(pTemp.parent.joinpath('10 Loc' + pNameCondensed + '.EnglishT'))

		pTemp = p.joinpath('mmmerge/Data/10LocLANG.EnglishT')
		if pTemp.exists():
			pTemp.rename(pTemp.parent.joinpath('10 Loc' + pNameCondensed + '.EnglishT'))

		for pTemp in getFilePaths(p.joinpath('mmmerge/Data/Text localization'), 'txt', True):
			if pTemp.name[:4] == 'LANG':
				pTemp.rename(pTemp.parent.joinpath(pNameCondensed + pTemp.name[4:]))

		for versionNum in ['6', '7', '8', 'merge']:
			pTemp = p.joinpath('mm' + versionNum + '/Data/LocalizeConf.ini')
			config = configparser.ConfigParser()
			config.optionxform = str # keep key case (the native renderer's keys are case-sensitive)
			config.read(pTemp, encoding = langEncDict[p.name])

			config['Settings']['game_version']     = versionNum                          # 6/7/8/merge

			if versionNum == 'merge':
				config['Settings']['grayface_version'] = versions['grayface']['8']           # GrayFace Patch's version
				config['Settings']['merge_version']    = versions['merge']                   # 0 (not mmmerge)/YYYY-MM-DD
			else:
				config['Settings']['grayface_version'] = versions['grayface'][versionNum]
				config['Settings']['merge_version']    = '0'

			config['Settings']['lang']             = p.name
			config['Settings']['i18n_version']     = versions['i18n'][p.name]
			config['Settings']['encoding']         = langEncDict[p.name]

			# global extra line spacing off by default; the 12px font carries
			# a per-font ",1" instead (see languages.dbcs_fonts / docs/dev/fonts.md)
			if p.name in dbcsLangs and 'mm' + versionNum in settings.native_dbcs_games:
				config['Settings']['lineSpacing'] = '0'

			with open(pTemp, mode = 'w', encoding = langEncDict[p.name]) as configfile:
				config.write(configfile, False)

			if p.name in dbcsLangs and 'mm' + versionNum in settings.native_dbcs_games:
				block = DBCS_FONT_TEMPLATE
				for name, value in LANGUAGES[p.name].get('dbcs_fonts', {}).items():
					block = block.replace('\n' + name + '=\n', '\n' + name + '=' + value + '\n')
				with open(pTemp, mode = 'a', encoding = langEncDict[p.name]) as configfile:
					configfile.write(block)

			rewriteProgramName(pTemp, langEncDict[p.name])

		if p.name in dbcsLangs:
			for versionNum in ['6', '7', '8', 'merge']:
				versionNum2 = versionNum
				if versionNum2 == 'merge':
					versionNum2 = '8'
				pTemp = p.joinpath('mm' + versionNum + '/mm' + versionNum2 + 'lang.ini')
				config = configparser.RawConfigParser()
				config.optionxform = str
				config.read(pTemp, encoding = langEncDict[p.name])

				for opt in ['RecoveryTimeInfo', 'PlayerNotActive', 'DoubleSpeed', 'NormalSpeed', 'GameSavedText', 'ArmorHalved']:
					if config.has_option('Settings', opt):
						config['Settings'][opt] = '.' + config['Settings'][opt]

				with open(pTemp, mode = 'w', encoding = langEncDict[p.name]) as configfile:
					config.write(configfile, False)

		for versionNum in ['6', '7', '8', 'merge']:
			pTemp = p.joinpath('mm' + versionNum)
			encoding = langEncDict[p.name]

			copyFonts(encoding, pTemp, versionNum, pNameCondensed)
			if encoding in dbcsEncs:
				copyFonts('cp1252', pTemp, versionNum, pNameCondensed)
				if 'mm' + versionNum in settings.native_dbcs_games:
					copyDbcsFonts(p.name, pTemp)
			if encoding == 'cp1252' or encoding in dbcsEncs:
				if versionNum == '6' or versionNum == '7':
					versionNumFont = '67'
				else: # versionNum == '8' or versionNum == 'merge'
					versionNumFont = '8'
				copyFonts('cp1252/' + versionNumFont, pTemp, versionNum, pNameCondensed)

	print('Main process is done.')


# scripts_datatables layout (single source of truth for shared files):
#   _common/_all/**     applied to every language x every game listed below
#   _common/<game>/**   applied to every language, that game only
#   <lang>/<game>/**    language-specific files (win over _common)
def processScriptsDatatables(postprodPath):
	sdtPath = Path(settings.non_text_folder).joinpath('scripts_datatables')
	commonPath = sdtPath.joinpath('_common')

	commonGames = []
	if commonPath.exists():
		commonGames = [p.name for p in getFilePaths(commonPath, '', False) if p.name != '_all']
		if commonPath.joinpath('_all').exists():
			commonGames = sorted(set(commonGames) | set(settings.script_games))

	for pntLang in getFilePaths(sdtPath, '', False):
		if pntLang.name == '_common':
			continue
		gameNames = sorted(set(p.name for p in getFilePaths(pntLang, '', False)) | set(commonGames))
		for gameName in gameNames:
			dest = postprodPath.joinpath(pntLang.name).joinpath(gameName)
			if commonPath.joinpath('_all').exists():
				copy_tree(commonPath.joinpath('_all'), dest)
			if commonPath.joinpath(gameName).exists():
				copy_tree(commonPath.joinpath(gameName), dest)
			if pntLang.joinpath(gameName).exists():
				copy_tree(pntLang.joinpath(gameName), dest)
	print('Script, datatable process is done.')


# img/prod layout: <lang>/<game>/Data/<archive dir>/... ; the pseudo-game
# folder mmmerge_and_mm8 is a single source shipped to both games
def processImages(postprodPath):
	for pntLang in getFilePaths(Path(settings.non_text_folder).joinpath('img/prod'), '', False):
		pntLangName = pntLang.name
		pntLangNameCondensed = pntLangName.upper().replace('_', '') # e.g. ZHCN
		for pntVer in getFilePaths(pntLang, '', False):
			if pntVer.name == 'mmmerge_and_mm8':
				gameNames = ['mmmerge', 'mm8']
			else:
				gameNames = [pntVer.name]
			# next(pntVer.iterdir()) is the first child dir of pntVer, it is assumed the only child dir pntVer is /Data/ folder since images store only in /Data/
			dataFolder = next(pntVer.iterdir())
			for gameName in gameNames:
				for dirTemp in getFilePaths(dataFolder, '', False):
					folderNameTemp = '10 Loc' + pntLangNameCondensed + '.' + dirTemp.name
					if dirTemp.name == 'icons' and gameName == 'mmmerge':
						folderNameTemp = 'z' + folderNameTemp
					pTemp = postprodPath.joinpath(pntLangName).joinpath(gameName).joinpath(dataFolder.name).joinpath(folderNameTemp)
					copy_tree(str(dirTemp), str(pTemp))
	print('Image process is done.')


def processMM8Setup(postprodPath):
	for pntLang in getFilePaths(Path(settings.non_text_folder).joinpath('MM8Setup/prod'), '', False):
		for pntVer in getFilePaths(pntLang, '', False):
			shutil.copy(pntVer.joinpath('MM8Setup.Exe'), postprodPath.joinpath(pntLang.name).joinpath(pntVer.name))
	print('MM8Setup process is done.')


def processSound(postprodPath):
	for pntLang in getFilePaths(Path(settings.non_text_folder).joinpath('sound/prod'), '', False):
		pntLangName = pntLang.name
		for pntVer in getFilePaths(pntLang, '', False):
			soundParentFolder = next(pntVer.iterdir())
			soundFolder = next(soundParentFolder.iterdir())

			folderNameTemp = '10 Loc' + pntLangName.upper().replace('_', '') + '.' + soundFolder.name
			pTemp = postprodPath.joinpath(pntLangName).joinpath(pntVer.name).joinpath(soundParentFolder.name).joinpath(folderNameTemp)
			copy_tree(str(soundFolder), str(pTemp))

			# zh_TW reuses the zh_CN voice-over recordings
			if pntLangName == 'zh_CN':
				folderNameTempZHTW = '10 LocZHTW.' + soundFolder.name
				pTempZHTW = postprodPath.joinpath('zh_TW').joinpath(pntVer.name).joinpath(soundParentFolder.name).joinpath(folderNameTempZHTW)
				copy_tree(str(soundFolder), str(pTempZHTW))

	print('Sound process is done.')


# pack every '10 Loc*' asset folder into its mm archive (.lod/.snd)
def packArchives(postprodPath):
	for pntLang in getFilePaths(postprodPath, '', False):
		for pntVer in getFilePaths(pntLang, '', False):
			dataFolder = pntVer.joinpath('Data')
			soundFolder = pntVer.joinpath('Sounds')
			fInFolder = []
			if dataFolder.exists():
				fInFolder = fInFolder + getFilePaths(dataFolder, '', False)
			if soundFolder.exists():
				fInFolder = fInFolder + getFilePaths(soundFolder, '', False)
			for fInDataFolder in fInFolder:
				if fInDataFolder.name[0:6] == '10 Loc' or fInDataFolder.name[0:7] == 'z10 Loc':
					stemTemp = fInDataFolder.name.split('.')[-1].lower()
					if stemTemp == 'audio':
						archiveType = 'mmsnd'
						archiveExt = 'snd'
					elif stemTemp == 'icons' or stemTemp == 'events':
						archiveType = 'mmiconslod'
						archiveExt = 'lod'
					elif stemTemp == 'englishd' or stemTemp == 'englisht':
						archiveType = 'mm8loclod'
						archiveExt = 'lod'
					else:
						raise ValueError('Unknown archive folder type: ' + str(fInDataFolder))
					mmarch('c', fInDataFolder.name + '.' + archiveExt, archiveType, str(fInDataFolder.parent), str(fInDataFolder) + '\\*')
					mmarch('o', str(fInDataFolder.parent.joinpath(fInDataFolder.name + '.' + archiveExt)))
					shutil.rmtree(str(fInDataFolder))
					print(str(fInDataFolder.parent.joinpath(fInDataFolder.name + '.' + archiveExt)) + ' is made.')


def run():
	postprodPath = Path(settings.postprod_folder)
	prodPath = Path(settings.prod_folder)

	processProdText(postprodPath, prodPath)
	processScriptsDatatables(postprodPath)
	processImages(postprodPath)
	processMM8Setup(postprodPath)
	processSound(postprodPath)
	packArchives(postprodPath)

	# TODO: non_text/video/zh_CN -> Anims/10 LocZHCN.Magicdod.vid
