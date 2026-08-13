# getFilePaths
# By Tom CHEN <tomchen.org@gmail.com> (tomchen.org)

# `extension` can be a tring or a list of strings
# for each extension string:
# - if it starts and ends with double quote, then it is treated as a file name
# - if it starts with *, then it is treated as a glob pattern with wildcard
# - if it is an empty string '', then it is treated as "all files"
# - otherwise, it is treated as a file extension

import re
import os

def getFilePaths(pathObj, extension = 'txt', recursive = True, includeFolder = True):
	if recursive:
		pathPre = '**/'
	else:
		pathPre = ''
	if type(extension) is list:
		retList = []
		for thisExt in extension:
			retList += getFilePaths(pathObj, extension = thisExt, recursive = recursive)
		return retList
	else:
		fileName = ''
		if extension == '':
			fileName = '*'
		elif re.match(r'^".*"$', extension):
			fileName = extension[1:-1]
		elif re.match(r'^\*', extension):
			fileName = extension
		else:
			fileName = '*.' + extension

		if includeFolder:
			return list(pathObj.glob(pathPre + fileName))
		else:
			files = pathObj.glob(pathPre + fileName)
			return [f for f in files if os.path.isfile(f)]
