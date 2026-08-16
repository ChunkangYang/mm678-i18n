# Batch Add Context: template_without_context -> template (with context)
# By Tom CHEN <tomchen.org@gmail.com> (tomchen.org)

import re
from pathlib import Path

from .getfilepaths import getFilePaths
from config import settings


def addContext(inputPath, outputPath, encoding, context):
	f = inputPath.open(mode = 'r', encoding = encoding, newline = '', errors = "strict")
	content = f.read()
	f.close()
	content = content.replace("_(TRANS)_", "_(TRANS_CONTEXT:'" + context + "')_")
	outputPath.parent.mkdir(parents = True, exist_ok = True)
	fout = outputPath.open(mode = 'w', encoding = encoding, newline = '', errors = "strict")
	content = fout.write(content)
	fout.close()


def batchAddContext(inputPath, extension, encoding, outputPath, filePathToContextFunc):
	for p in getFilePaths(inputPath, extension = extension):
		addContext(inputPath = p, outputPath = outputPath.joinpath(p.relative_to(inputPath)), encoding = encoding, context = filePathToContextFunc(p))


def fn2c(filePath):
	fileName = filePath.name.lower()
	ext = filePath.suffix.lower()
	stem = filePath.stem.lower()

	if fileName == 'intro.str' or fileName == 'lose.str' or fileName == 'win.str':
		return fileName
	elif ext == '.str' or fileName == 'mapstats.txt' or fileName == 'lang_mapstats.txt' or fileName == 'localizetables.lang_2devents.txt' or fileName == 'lang_2devents.txt' or fileName == '2devents.txt':
		return 'location'
	elif fileName == 'localizetables.lang_itemstxt.txt' or fileName == 'lang_itemstxt.txt' or fileName == 'useitems.txt':
		return 'items'
	elif fileName == 'localizetables.lang_monsters.txt' or fileName == 'lang_monsters.txt':
		return 'monsters'
	elif fileName == 'npcbtb.txt' or fileName == 'npctext.txt' or fileName == 'lang_npctext.txt' or fileName == 'npcgreet.txt' or fileName == 'npcnews.txt' or fileName == 'proftext.txt' \
			or fileName == 'lang_npcgreet1.txt' or fileName == 'lang_npcgreet2.txt' or fileName == 'lang_npcnews.txt' \
			or fileName == 'lang_npcnewstopics.txt':
		return 'npc conversation'
	# the LocEN-template runtime tables keep their historical contexts so
	# translations carry over from the pre-restructure file names
	elif fileName == 'lang_messagescrolls.txt':
		return 'scroll'
	elif fileName == 'lang_autonotetxt.txt' or fileName == 'lang_awardstxt.txt':
		return 'autonote or awards'
	elif fileName == 'lang_queststxt.txt':
		return 'quests'
	elif fileName == 'lang_classnames.txt' or fileName == 'lang_classdescriptions.txt':
		return 'class'
	elif fileName == 'lang_spcitemstxtnames.txt' or fileName == 'lang_spcitemstxtstats.txt':
		return 'spcitems'
	elif fileName == 'lang_stditemstxtnames.txt' or fileName == 'lang_stditemstxtstats.txt':
		return 'stditems'
	elif fileName == 'lang_transtxt.txt':
		return 'trans'
	elif fileName == 'lang_placemontxt.txt':
		return 'placemon'
	elif fileName == 'npcprof.txt':
		return 'npcprof'
	elif fileName == 'autonote.txt' or fileName == 'awards.txt':
		return 'autonote or awards'
	elif fileName == 'npcnames.txt' or fileName == 'pcnames.txt' or fileName == 'localizetables.lang_npcnames.txt' or fileName == 'lang_npcnames.txt':
		return 'npcnames'
	elif fileName == 'mm7history.txt' or fileName == 'history.txt':
		return 'history'
	elif ext == '.txt':
		if stem[0:5] == 'lang_':
			return stem[5:]
		else:
			return stem
	elif fileName == 'mm8lang.ini' or fileName == 'mm7lang.ini' or fileName == 'mm6lang.ini':
		return 'mm_lang.ini'
	elif fileName == 'localizeconf.ini':
		return 'localizeconf.ini'

def run():
	batchAddContext(
		inputPath = Path(settings.template_without_context_folder),
		extension = settings.file_extensions,
		encoding = settings.template_encoding,
		outputPath = Path(settings.template_folder),
		filePathToContextFunc = fn2c
	)
