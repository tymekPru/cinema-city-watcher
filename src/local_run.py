"""Lokalne uruchomienie: python src/local_run.py [--once] [--interval 60]"""

import argparse
import time

from watcher.runner import build, run_once


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Watcher biletów Cinema City (lokalnie)"
    )
    parser.add_argument("--once", action="store_true", help="jeden przebieg i koniec")
    parser.add_argument(
        "--interval", type=float, default=60, help="sekundy między przebiegami"
    )
    args = parser.parse_args()

    cfg, det, notifier = build()
    print(
        f"kino={cfg.cinema_id} film={cfg.film_id or cfg.film_match!r} attrs={cfg.required_attrs} "
        f"horyzont={cfg.horizon_days}d stan={cfg.state_backend} alerty={cfg.notify_backend}"
    )
    while True:
        n = run_once(det, notifier)
        print(f"[{time.strftime('%H:%M:%S')}] przebieg OK, alertów: {n}")
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
