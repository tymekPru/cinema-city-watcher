from .api import QuickbookApi
from .config import Config
from .detector import Detector
from .notify import make_notifier
from .state import make_state

SUBJECT = "cc-watcher: ruch na biletach!"


def build():
    cfg = Config()
    api = QuickbookApi(cfg.base_url, cfg.lang, cfg.request_gap_s)
    det = Detector(api, make_state(cfg), cfg)
    return cfg, det, make_notifier(cfg)


def run_once(det, notifier) -> int:
    """Jeden przebieg; wszystkie alerty idą w JEDNYM powiadomieniu."""
    alerts = det.sweep()
    if alerts:
        notifier.send(SUBJECT, "\n\n".join(alerts))
    return len(alerts)
