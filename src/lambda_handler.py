"""Wejście dla AWS Lambda (wyzwalane przez EventBridge Scheduler co minutę)."""

import time

from watcher.runner import build, run_once


def handler(event, context):
    cfg, det, notifier = build()
    total = run_once(det, notifier)
    sweeps = 1
    # tryb intensywny (środowe okno dropów): kręć się do końca czasu Lambdy
    while (
        cfg.intensive
        and context.get_remaining_time_in_millis()
        > (cfg.intensive_interval_s + 15) * 1000
    ):
        time.sleep(cfg.intensive_interval_s)
        total += run_once(det, notifier)
        sweeps += 1
    return {"sweeps": sweeps, "alerts": total}
