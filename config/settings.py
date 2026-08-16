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

template_folder = 'build/templates_ctx'             # templates with context markers
dev_folder      = 'build/dev'                       # .py files with gettext calls (Poedit scans these)
prod_folder     = 'build/prod'                      # translated game text
postprod_folder = 'build/postprod'                  # installable file trees
release_build_folder = 'build/release'              # release working dirs + final .zip in out/

# external tool: mmarch (MM archive packer, github.com/might-and-magic/mmarch)
# installed via npm (`npm i -g mmarch`) and resolved from PATH
mmarch_exe = 'mmarch'

# games that ship MMExtension Lua scripts / data tables
# (the scripts_datatables/_common/_all tree is applied to each of these)
script_games = ['mm6', 'mm7', 'mm8', 'mmmerge']

# games whose DBCS-language builds use the native renderer (FNT_DBCS.lua):
# their text ships as plain DBCS bytes (no dbcs_special marker encoding) and
# their LocalizeConf.ini gets the [dbcsFont] template. FNT_DBCS.lua supports
# all three engines (smoke-tested in-game 2026-08-15).
native_dbcs_games = ['mm6', 'mm7', 'mm8', 'mmmerge']

file_extensions = ['txt', 'str', 'ini']

# source files offer translatable strings but not the format
# all text to the right of the rightmost template_repl tag won't be taken into consideration
template_repl = "_(TRANS)_"
template_repl_with_context = "_(TRANS_CONTEXT:'<context>')_" # translatable text with context
template_encoding = 'UTF-8' # default is 'UTF-8'

first_language = 'en'

source_encoding = languages.source_encoding # defaults are 'UTF-8'

encoding_errors_handling = 'strict' # could be 'strict', 'ignore' (default), 'replace', 'backslashreplace', etc. see https://docs.python.org/3/library/io.html#io.TextIOWrapper

# (the custom_list/conflict_priority settings for the legacy bootstrap
# extraction were removed; references/notes/zh keeps the old override lists
# as an archive — their decisions are baked into the zh_CN .po)

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