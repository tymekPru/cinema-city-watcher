import sys
from pathlib import Path

# testy odpalamy z katalogu repo: "import watcher" ma dzialac bez instalacji pakietu
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
