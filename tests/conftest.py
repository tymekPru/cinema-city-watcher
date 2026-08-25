import sys
from pathlib import Path

# Tests run from the repository root: make "import watcher" work without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
