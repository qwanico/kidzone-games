"""Make the KidZone game packages importable from the tests directory.

The web builds live in per-app folders (KidZoneWeb, ArcadeWeb) rather than an
installed package, so pytest needs those roots on sys.path before it can
import `games.common.*`.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

for app in ("KidZoneWeb", "ArcadeWeb"):
    app_root = str(REPO_ROOT / app)
    if app_root not in sys.path:
        sys.path.insert(0, app_root)
