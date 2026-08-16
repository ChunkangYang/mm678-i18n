# mm678 — the single command-line entry point for the whole build pipeline.
#
# Pipeline overview:
#
#   templates : template_without_context -> template   (context markers added)
#   dev       : template + source(en)    -> dev .py files (gettext calls)
#   [translators update .po from dev via Poedit; `new-language` scaffolds
#    an empty .po for a language that doesn't have one yet]
#   mo        : .po -> .mo               (gettext compile)
#   prod      : .mo + dev -> translated game text files
#   postprod  : prod + fonts/scripts/images/sounds -> installable file trees
#   installers: postprod + additional files -> NSIS setup .exe -> .7z
#
#   build     = mo + prod + postprod + installers  (the one-click build)

import argparse
import sys

from . import __version__, paths


def cmd_templates(args):
	from . import context
	context.run()

def cmd_dev(args):
	from . import pipeline
	pipeline.generateDevOnly()

def cmd_update_po(args):
	from . import pipeline
	pipeline.updatePo()

def cmd_mo(args):
	from . import pipeline
	pipeline.po2Mo()

def cmd_prod(args):
	from . import pipeline
	pipeline.generateProd()

def cmd_postprod(args):
	from . import postprod
	postprod.run()

def cmd_installers(args):
	from . import setup_builder
	setup_builder.run(args.steps)

def cmd_build(args):
	from . import pipeline, postprod, setup_builder
	pipeline.po2Mo()
	pipeline.generateProd()
	postprod.run()
	if args.no_installers:
		print('Skipped installers (--no-installers).')
	else:
		setup_builder.run()

def cmd_new_language(args):
	from . import pipeline
	pipeline.newLanguage(args.lang)

def cmd_zhconvert(args):
	from . import zhconvert
	zhconvert.run(method = args.method)

def cmd_check(args):
	from . import checks
	sys.exit(1 if checks.run(args.names or None) else 0)

def cmd_version(args):
	from config.versions import versions, i18n_release
	print('mm678-i18n pipeline ' + __version__)
	print('GrayFace patch versions: ' + str(versions['grayface']))
	print('MM Merge version: ' + versions['merge'])
	print('i18n release: ' + i18n_release['date'] + ' (' + i18n_release['dot'] + ')')


def main():
	parser = argparse.ArgumentParser(
		prog = 'mm678',
		description = 'Build pipeline for the Might and Magic 6/7/8 localization project.')
	sub = parser.add_subparsers(dest = 'command', required = True)

	sub.add_parser('templates', help = 'generate context-annotated templates').set_defaults(func = cmd_templates)
	sub.add_parser('dev', help = 'generate dev .py files (the Poedit source-scan target)').set_defaults(func = cmd_dev)

	sub.add_parser('update-po', help = 'non-destructively update all .po after template/source '
		'changes (translations kept; new strings added untranslated, removed ones marked obsolete; '
		'GNU msgmerge on PATH enables fuzzy matching)').set_defaults(func = cmd_update_po)
	sub.add_parser('mo', help = 'compile .po -> .mo (derived languages regenerated first)').set_defaults(func = cmd_mo)
	sub.add_parser('prod', help = 'generate translated game text files from .mo').set_defaults(func = cmd_prod)
	sub.add_parser('postprod', help = 'assemble installable file trees (text + fonts, scripts, images, sounds)').set_defaults(func = cmd_postprod)

	p = sub.add_parser('installers', help = 'build the NSIS installers (.exe), extract-over .zip archives, and .7z archives')
	p.add_argument('--steps', nargs = '+', choices = ['compose', 'zip', 'makensis', 'collect', 'compress'],
		help = 'run only these steps (default: all)')
	p.set_defaults(func = cmd_installers)

	p = sub.add_parser('build', help = 'one-click build: mo + prod + postprod + installers')
	p.add_argument('--no-installers', action = 'store_true',
		help = 'stop after postprod (no NSIS/7-Zip needed)')
	p.set_defaults(func = cmd_build)

	p = sub.add_parser('new-language', help = 'create an empty .po for a new language '
		'(translate it in Poedit from there)')
	p.add_argument('lang', help = 'language code, e.g. fr, de, ru, ja')
	p.set_defaults(func = cmd_new_language)

	p = sub.add_parser('zhconvert', help = 'regenerate the zh_TW .po from the zh_CN .po via OpenCC')
	p.add_argument('--method', default = 's2twp', help = 'OpenCC conversion method (default: s2twp)')
	p.set_defaults(func = cmd_zhconvert)

	p = sub.add_parser('check', help = 'run quality checks (default: po, encoding, linelength; '
		'"lf" is an opt-in diagnostic — bare LF in strings is a legitimate soft line break)')
	p.add_argument('names', nargs = '*', choices = ['po', 'encoding', 'lf', 'linelength'],
		help = 'checks to run')
	p.set_defaults(func = cmd_check)

	sub.add_parser('version', help = 'print pipeline and game/patch versions').set_defaults(func = cmd_version)

	args = parser.parse_args()

	# all pipeline paths are repo-root-relative
	paths.chdir_repo_root()
	args.func(args)
