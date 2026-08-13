# Repository-root anchoring.
#
# Importing this module makes the repo root importable (for the `config`
# package) regardless of how mm678i18n itself was imported. The pipeline
# modules use repo-root-relative paths, so callers must also run with the
# repo root as working directory — the CLI takes care of that via chdir().

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(REPO_ROOT))


def chdir_repo_root():
	os.chdir(REPO_ROOT)
