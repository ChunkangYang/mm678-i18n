# Game/patch versions and the release matrix.
# The data half lives in versions.toml; this module loads it and derives
# the per-language i18n version table. Language-specific metadata
# (encodings, per-language versions) lives in config/languages.toml.

import tomllib
from pathlib import Path

from config.languages import LANGUAGES, langEncDict, dbcsLangs, dbcsEncs  # noqa: F401 (re-exported)

with open(Path(__file__).with_name('versions.toml'), 'rb') as _f:
	_data = tomllib.load(_f)

versions = {
	'grayface': _data['grayface_versions'],
	'merge': _data['merge_version'],
	# per-language i18n version (last-update date, from languages.toml)
	'i18n': {lang: meta['i18n_version'] for lang, meta in LANGUAGES.items()},
}

# the date goes into the release archive names
i18n_release = {
	'date': _data['release_date'],
}

# one dict per produced .zip archive (lang/target/game/outname);
# see versions.toml for the field docs
releases = _data['releases']
