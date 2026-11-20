from datetime import timedelta
from pathlib import Path

from .alerts import AlertStore
from .api import QuickbookApi
from .config import Config, ConfigError
from .detector import HORIZON_DAYS, Detector, today
from .notify import make_notifier
from .state import FileState


class App:
    def __init__(self, config_path) -> None:
        self.config_path = Path(config_path)
        self.reload()

    def reload(self) -> None:
        cfg = Config(self.config_path)
        self.cfg = cfg
        self.apis = {
            code: QuickbookApi(c.base_url, c.lang, cfg.request_gap_s, cfg.cache_s)
            for code, c in cfg.countries.items()
        }
        self.alerts = AlertStore(cfg.alerts_file)
        self.state = FileState(cfg.state_file)
        self.detector = Detector(cfg.min_ratio_delta, cfg.cooldown_min)
        self.notifier = make_notifier(cfg)
        self._loaded_mtime = self.config_path.stat().st_mtime_ns

    def reload_if_changed(self) -> None:
        """Pick up edits made to appsettings.json (for example from the UI) between sweeps."""
        try:
            mtime = self.config_path.stat().st_mtime_ns
        except OSError:
            return
        if mtime == self._loaded_mtime:
            return
        try:
            self.reload()
            print("[info] settings reloaded")
        except ConfigError as exc:
            print(f"[warn] settings not reloaded: {exc}")

    def run_once(self) -> int:
        """Sweep every active alert. Each alert with changes gets one notification."""
        self.reload_if_changed()
        day = today()
        alerts = self.alerts.load()
        state = self.state.load()
        on_sale: dict = {}
        total = 0
        for alert in alerts:
            if alert.get("dateTo") and alert["dateTo"] < day.isoformat():
                continue
            api = self.apis.get(alert["country"])
            if api is None:
                print(f"[warn] {alert['id']}: unknown country {alert['country']!r}, skipped")
                continue
            if alert["country"] not in on_sale:
                on_sale[alert["country"]] = self._films_on_sale(api, day)
            texts = self.detector.sweep(
                api, alert, state.setdefault(alert["id"], {}), day, on_sale[alert["country"]]
            )
            if texts:
                subject = f"{alert['film']['name']} @ {alert['cinema']['name']}"
                self.notifier.send(subject, "\n\n".join(texts))
                total += len(texts)
        for stale in [k for k in state if k not in {a["id"] for a in alerts}]:
            del state[stale]
        self.state.save(state)
        return total

    @staticmethod
    def _films_on_sale(api, day):
        """Ids of films with any ticket on sale, fetched once per country per sweep."""
        until = (day + timedelta(days=HORIZON_DAYS)).isoformat()
        try:
            return {f["id"] for f in api.films(until, fresh=True)}
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] film list unavailable, scanning cinemas anyway: {exc}")
            return None


def build(config_path) -> App:
    return App(config_path)
