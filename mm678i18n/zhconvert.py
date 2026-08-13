# ZhConvert: regenerate the zh_TW .po from the zh_CN .po via OpenCC
# (Simplified -> Traditional (Taiwan) conversion + project word fixes)

import time
from pathlib import Path

import polib

from . import paths  # noqa: F401
from config import settings

quoteDict = {
	'「': '“',
	'」': '”',
	'『': '‘',
	'』': '’',
}

# word replacements applied BEFORE the OpenCC conversion (Simplified forms)
replaceWordList = [['自由天堂', '自由港'], ['恩洛斯', '安罗斯'], ['贾丹姆', '贾达密'], ['咔', '咯'], ['～', '-']]
# word replacements applied AFTER the OpenCC conversion (Traditional forms)
replaceWordListAfter = [['心繫', '心系']]


# method:
# hk2s: Traditional Chinese (Hong Kong standard) to Simplified Chinese
# s2hk: Simplified Chinese to Traditional Chinese (Hong Kong standard)
# s2t: Simplified Chinese to Traditional Chinese
# s2tw: Simplified Chinese to Traditional Chinese (Taiwan standard)
# s2twp: Simplified Chinese to Traditional Chinese (Taiwan standard, with phrases)
# t2hk: Traditional Chinese to Traditional Chinese (Hong Kong standard)
# t2s: Traditional Chinese to Simplified Chinese
# t2tw: Traditional Chinese to Traditional Chinese (Taiwan standard)
# tw2s: Traditional Chinese (Taiwan standard) to Simplified Chinese
# tw2sp: Traditional Chinese (Taiwan standard) to Simplified Chinese (with phrases)
def run(method = 's2twp', convertQuote = True, sourceLang = 'zh_CN', targetLang = 'zh_TW'):
	from opencc import OpenCC # imported lazily: only this command needs OpenCC

	start = time.time()
	cc = OpenCC(method)

	i18nPath = Path(settings.i18n_folder)
	sourcePo = i18nPath.joinpath(sourceLang).joinpath('LC_MESSAGES').joinpath(settings.textdomain + '.po')
	targetPo = i18nPath.joinpath(targetLang).joinpath('LC_MESSAGES').joinpath(settings.textdomain + '.po')

	po = polib.pofile(str(sourcePo))
	for entry in po:
		outputContent = entry.msgstr

		for replaceWord in replaceWordList:
			outputContent = outputContent.replace(replaceWord[0], replaceWord[1])

		outputContent = cc.convert(outputContent)

		for replaceWordAfter in replaceWordListAfter:
			outputContent = outputContent.replace(replaceWordAfter[0], replaceWordAfter[1])

		if convertQuote:
			if method in ['hk2s', 't2s', 'tw2s', 'tw2sp']:
				QDict = quoteDict
			elif method in ['s2hk', 's2t', 's2tw', 's2twp']:
				QDict = dict([[v, k] for k, v in quoteDict.items()])
			else:
				QDict = {}
			for q in QDict:
				outputContent = outputContent.replace(q, QDict[q])

		entry.msgstr = outputContent

	po.metadata['Language'] = targetLang
	targetPo.parent.mkdir(parents = True, exist_ok = True)
	po.save(str(targetPo))

	print('Execution time: ' + str(time.time() - start) + ' second')
