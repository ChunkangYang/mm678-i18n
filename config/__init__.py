# Project configuration package for mm678-i18n.
#
# Each area is a .toml (the editable data) + a .py (loads the TOML and
# derives lookup tables; its module API is what the pipeline imports):
#
# languages.toml/.py — per-language metadata (encodings, versions, DBCS
#                      fonts): the single source of truth for anything
#                      language-specific
# versions.toml/.py  — game/patch versions and the release matrix
# settings.toml/.py  — text-pipeline settings consumed by mm678i18n.pipeline
