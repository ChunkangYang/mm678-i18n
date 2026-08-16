# Text-pipeline settings, consumed by mm678i18n.pipeline.
# The static values live in settings.toml — every key there becomes an
# attribute of this module; only derived values are defined below.
# Per-language encodings are derived from config/languages.toml (single
# source of truth) — edit them there, not here.

import tomllib
from pathlib import Path

from config import languages

with open(Path(__file__).with_name('settings.toml'), 'rb') as _f:
	globals().update(tomllib.load(_f))

# source-folder encoding per language where it is not UTF-8 (defaults are UTF-8)
source_encoding = languages.source_encoding
