import subprocess
import sys
from pathlib import Path

from watcher.lock import SweepBusy, SweepLock

CHILD = """
import sys; sys.path.insert(0, {src!r})
from watcher.lock import SweepBusy, SweepLock
try:
    SweepLock({path!r}).acquire(wait=False); print("free")
except SweepBusy:
    print("busy")
"""


def _probe(path):
    src = str(Path(__file__).resolve().parents[1] / "src")
    return subprocess.run([sys.executable, "-c", CHILD.format(src=src, path=str(path))], capture_output=True, text=True).stdout.strip()


def test_lock_is_exclusive_across_processes(tmp_path):
    path = tmp_path / "sweep.lock"
    lock = SweepLock(path)
    with lock:
        assert _probe(path) == "busy"
    assert _probe(path) == "free"


def test_non_blocking_acquire_raises_when_held(tmp_path):
    first, second = SweepLock(tmp_path / "l"), SweepLock(tmp_path / "l")
    first.acquire()
    try:
        import pytest

        with pytest.raises(SweepBusy):
            second.acquire(wait=False)
    finally:
        first.release()
    second.acquire(wait=False)
    second.release()
