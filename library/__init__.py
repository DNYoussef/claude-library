from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path


# Treat the repo root as part of the "library" namespace so imports like
# `library.common` resolve to the top-level `common` folder.
__path__ = extend_path(__path__, __name__)
__path__.append(str(Path(__file__).resolve().parent.parent))
