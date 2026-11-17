"""Cinema City ticket watcher.

    python src/main.py               one sweep over all alerts, then exit (cron-friendly)
    python src/main.py --keep-alive  sweep, sleep runtime.pollIntervalSeconds, repeat

Settings are read from appsettings.json in the repository root unless --config
points elsewhere. Alerts are managed through the web UI (src/serve.py).
"""

import argparse
import sys
import time
from pathlib import Path

from watcher.config import ConfigError
from watcher.runner import build

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "appsettings.json"


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cinema City ticket watcher")
    parser.add_argument(
        "--keep-alive",
        action="store_true",
        help="keep running and poll again every runtime.pollIntervalSeconds "
        "(default: run a single sweep and exit)",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="path to the settings file (default: %(default)s)",
    )
    return parser.parse_args(argv)


def _ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        app = build(args.config)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    cfg = app.cfg
    mode = f"keep-alive every {cfg.poll_interval_s:g}s" if args.keep_alive else "once"
    print(
        f"config={cfg.path} alerts={len(app.alerts.load())} "
        f"data={cfg.data_dir} mode={mode}"
    )

    if not args.keep_alive:
        n = app.run_once()
        print(f"[{_ts()}] sweep done, alerts: {n}")
        return 0

    try:
        while True:
            try:
                n = app.run_once()
                print(f"[{_ts()}] sweep done, alerts: {n}")
            except Exception as exc:  # noqa: BLE001
                print(f"[{_ts()}] sweep failed: {exc}", file=sys.stderr)
            time.sleep(cfg.poll_interval_s)
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
