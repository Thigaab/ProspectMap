"""Add `cli/` to sys.path so flat imports (`import config`, `from cache import ...`)
work from the API package.

`cli/` deliberately has no __init__.py (see CLAUDE.md) so it isn't importable
as a package — the CLI relies on Python putting the script's directory on
sys.path. The API doesn't run cli scripts, so we replicate the same trick.
"""
import sys
from pathlib import Path

CLI_DIR = Path(__file__).resolve().parent.parent / "cli"
if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))
