# Text-pipeline settings, consumed by mm678i18n.pipeline.
# Per-language encodings are derived from config/languages.py (single source
# of truth) — edit them there, not here.

from config import languages

project_name = 'Might and Magic 6 7 8 Translation'
author_name  = 'Tom Chen'
author_email = 'tomchen.org@gmail.com'
team_name    = 'Might and Magic Unofficial Translation Team'
textdomain = 'mm678'

# folders (no trailing slash); everything under build/ is generated and
# safe to delete at any time
source_folder   = 'source'                          # original game text per language (tracked)
template_without_context_folder = 'templates'       # templates without context markers (tracked)
i18n_folder     = 'translations'                    # gettext .pot/.po (tracked; .mo generated)
non_text_folder = 'assets'                          # fonts, images, scripts, sounds (tracked)
installer_folder = 'installer'                      # NSIS scripts + additional files (tracked)

template_folder = 'build/templates_ctx'             # templates with context markers
dev_folder      = 'build/dev'                       # .py files with gettext calls (Poedit scans these)
prod_folder     = 'build/prod'                      # translated game text
postprod_folder = 'build/postprod'                  # installable file trees
setup_build_folder = 'build/setup'                  # installer working dirs + final .exe/.7z in out/

# external tool: mmarch (MM archive packer, github.com/might-and-magic/mmarch)
mmarch_exe = 'vendor/mmarch.exe'

# games that ship MMExtension Lua scripts / data tables
# (the scripts_datatables/_common/_all tree is applied to each of these)
script_games = ['mm8', 'mmmerge']

file_extensions = ['txt', 'str', 'ini']

# source files offer translatable strings but not the format
# all text to the right of the rightmost template_repl tag won't be taken into consideration
template_repl = "_(TRANS)_"
template_repl_with_context = "_(TRANS_CONTEXT:'<context>')_" # translatable text with context
template_encoding = 'UTF-8' # default is 'UTF-8'

first_language = 'en'

source_encoding = languages.source_encoding # defaults are 'UTF-8'

encoding_errors_handling = 'strict' # could be 'strict', 'ignore' (default), 'replace', 'backslashreplace', etc. see https://docs.python.org/3/library/io.html#io.TextIOWrapper

custom_list = {
	'zh_CN': {
		# 'my_translation_zh_0': [
		# 	# ['pet', '家养动物'],
		# 	[('cat', 'abbr for category'), '类别']
		# ], # can also be a string indicating the path to a tab-seperated file
		'customlist_zh_longstrfix': {
			'file': 'source/zh_CN/customlist/longstrfix.list',
			# 'encoding': 'UTF-8'
		},
		'customlist_zh_globalfix': {
			'file': 'source/zh_CN/customlist/globalfix.list',
			# 'encoding': 'UTF-8'
		},
		'customlist_zh_riddle': {
			'file': 'source/zh_CN/customlist/riddle.list',
			# 'encoding': 'UTF-8'
		},
		'customlist_zh_customlist': {
			'file': 'source/zh_CN/customlist/customlist.list',
			# 'encoding': 'UTF-8'
		},
		'customlist_zh_untrans': {
			'file': 'source/zh_CN/customlist/untrans.list',
			# 'encoding': 'UTF-8'
		},
		'customlist_zh_npctextnew': {
			'file': 'source/zh_CN/customlist/npctextnew.list',
			# 'encoding': 'UTF-8'
		}
	}
}

conflict_priority = {
	'zh_CN': [
		['CUSTOMLIST:customlist_zh_longstrfix'],
		['CUSTOMLIST:customlist_zh_globalfix'],
		['CUSTOMLIST:customlist_zh_riddle'],
		['CUSTOMLIST:customlist_zh_customlist'],
		['CUSTOMLIST:customlist_zh_untrans'],
		['CUSTOMLIST:customlist_zh_npctextnew'],
		['L1FOLDER:mmmerge', 'L1FOLDER:mm6', 'L1FOLDER:mm7', 'L1FOLDER:mm8'],
		['MOSTFREQUENT']
	]
}

# Language exclusion list containing languages present in the source folder, but do not need to proceed and generate i18n files
# default is []
# the first language cannot be excluded even if you put it in the list
i18n_language_exclusion = []

# Language exclusion list containing languages present in the i18n folder, but do not need to proceed and generate prod files
# default is []
# the first language could be excluded
prod_language_exclusion = []

separator = '\t'
eol = '\r\n'

# The following mode read non CRLF ('\r\n') LF ('\n') in translatable strings as `Slash N` ('\\n') at the beginning
# and convert them back at the end when generating prod files
# default is False
# effective only when eol = '\r\n'
lf_in_crlf_mode = True

# For every separator-separated value, you could do following trim, sanitization works
trim_whitespace = False
trim_doublequote = True
trim_singlequote = False
convert_two_quotes_to_one = True # convert "" (or '') to " (or ')

no_log = True
no_warning = True