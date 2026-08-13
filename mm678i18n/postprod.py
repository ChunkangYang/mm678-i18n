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


def mmarch(*args):
	subprocess.run([str(Path(settings.mmarch_exe).resolve())] + list(args), check = True)


def copyFonts(d, pTemp, mmVersion, pNameCondensed):
	if mmVersion == '6':
		targetLod = 'icons'
	elif mmVersion == '7':
		targetLod = 'events'
	else: # 8 or merge
		targetLod = 'EnglishT'
	for fnt in getFilePaths(Path(settings.non_text_folder).joinpath('font').joinpath(d), 'fnt', False):
		shutil.copy(fnt, pTemp.joinpath('Data/10 Loc' + pNameCondensed + '.' + targetLod))


# patch the per-language `local fontSizes = {...}` line into the shared
# FNT_DBCS.lua (the file itself is a single canonical copy in
# scripts_datatables/_common/_all/)
def patchFntDbcsFontSizes(gameDir, lang):
	sizes = LANGUAGES.get(lang, {}).get('fnt_dbcs_font_sizes')
	if sizes is None:
		return
	p = gameDir.joinpath('Scripts/General/FNT_DBCS.lua')
	if not p.is_file():
		return
	content = p.read_bytes()
	replacement = ('local fontSizes = {' + ', '.join(map(str, sizes)) + '}').encode('ascii')
	newContent, n = re.subn(rb'local fontSizes = \{[^}]*\}', replacement, content, count = 1)
	if n != 1:
		raise ValueError('fontSizes line not found in ' + str(p))
	p.write_bytes(newContent)


def processProdText(postprodPath, prodPath):
	if postprodPath.exists():
		shutil.rmtree(postprodPath)

	for p in getFilePaths(prodPath, '', True):
		if p.name == 'nonprod' and p.exists():
			shutil.rmtree(p)

	for p in getFilePaths(prodPath, '', False):
		if p.name in dbcsLangs:
			encodeDbcsSpecialFile(p, postprodPath.joinpath(p.name), langEncDict[p.name])
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

			with open(pTemp, mode = 'w', encoding = langEncDict[p.name]) as configfile:
				config.write(configfile, False)

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
			patchFntDbcsFontSizes(dest, pntLang.name)
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
