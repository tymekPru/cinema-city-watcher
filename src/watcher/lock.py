"""One sweep at a time, across processes.

The watcher (cron, --keep-alive or a container) and the UI's "Run now" button
all call App.run_once. They may live in different processes, so an advisory
file lock in the data directory keeps them from sweeping at once. The lock is
released automatically when the holder exits, even if it crashes.
"""

from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None


class SweepBusy(RuntimeError):
    pass


class SweepLock:
    def __init__(self, path) -> None:
        self.path = Path(path)
        self._fh = None

    def acquire(self, wait: bool = True) -> None:
        """Block until the lock is free, or raise SweepBusy when `wait` is False."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self.path, "a+")  # noqa: SIM115 - kept open while the lock is held
        if fcntl is not None:
            flags = fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB)
            try:
                fcntl.flock(fh, flags)
            except BlockingIOError:
                fh.close()
                raise SweepBusy("another sweep is running") from None
        self._fh = fh

    def release(self) -> None:
        if self._fh is None:
            return
        if fcntl is not None:
            fcntl.flock(self._fh, fcntl.LOCK_UN)
        self._fh.close()
        self._fh = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc) -> None:
        self.release()
