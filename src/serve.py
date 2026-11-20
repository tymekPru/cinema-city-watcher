"""Web UI for managing alerts.

    python src/serve.py [--config PATH]

Serves the static front-end from front/ and a small JSON API on top of the same
settings and data files the watcher uses. Standard library only.
"""

import argparse
import json
import mimetypes
import sys
import threading
import time
from datetime import timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from watcher.alerts import DuplicateAlert, validate
from watcher.config import ConfigError, read_editable, write_editable
from watcher.detector import today
from watcher.runner import App, build

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "appsettings.json"
FRONT_DIR = Path(__file__).resolve().parent.parent / "front"
FORMAT_GROUPS = ("screening-type", "special-type")
FORMAT_LABELS = {
    "2d": "2D",
    "3d": "3D",
    "4dx": "4DX",
    "imax": "IMAX",
    "70-mm": "70 mm",
    "screenx": "ScreenX",
    "vip": "VIP",
    "superscreen": "Superscreen",
    "infinity-vision": "Infinity Vision",
}


def _film_view(film: dict) -> dict:
    return {
        "id": film.get("id"),
        "name": film.get("name"),
        "releaseDate": (film.get("releaseDate") or "")[:10],
        "length": film.get("length"),
        "posterLink": film.get("posterLink"),
        "link": film.get("link"),
        "attributeIds": film.get("attributeIds", []),
        "languages": film.get("languages", {}),
        "comingSoon": False,
    }


def _coming_soon_view(poster: dict) -> dict:
    return {
        "id": poster.get("code"),
        "name": poster.get("featureTitle"),
        "releaseDate": (poster.get("dateStarted") or "")[:10],
        "length": None,
        "posterLink": poster.get("posterSrc"),
        "link": poster.get("url"),
        # Poster attributes carry genres and age ratings, not screening formats.
        "attributeIds": [],
        "languages": poster.get("languages", {}),
        "comingSoon": True,
    }


def _films(api, until: str) -> list[dict]:
    """Films on sale followed by announced ones, nearest release first."""
    films = [_film_view(f) for f in api.films(until)]
    known = {f["id"] for f in films}
    try:
        posters = api.coming_soon()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] coming-soon list unavailable: {exc}")
        posters = []
    soon = [
        _coming_soon_view(p)
        for p in posters
        if p.get("code") and p.get("code") not in known and p.get("filmShowingType", "FUTURE") == "FUTURE"
    ]
    return films + sorted(soon, key=lambda f: f["releaseDate"])


def _cinemas(api, until: str, formats: list[dict]) -> list[dict]:
    """Cinemas with the screening formats each one currently offers."""
    by_format = {f["id"]: {c["id"] for c in api.cinemas(until, f["id"])} for f in formats}
    return [
        {
            "id": c["id"],
            "name": c["displayName"],
            "imax": c["id"] in by_format.get("imax", ()),
            "formats": [fid for fid, ids in by_format.items() if c["id"] in ids],
        }
        for c in api.cinemas(until)
    ]


def _formats(attribute_groups: list[dict]) -> list[dict]:
    ids = []
    for group in attribute_groups:
        if group.get("group-name") in FORMAT_GROUPS:
            ids += [item["id"] for item in group.get("items", []) if item.get("id")]
    return [
        {"id": i, "label": FORMAT_LABELS.get(i, i.replace("-", " ").title())} for i in ids
    ]


class Handler(BaseHTTPRequestHandler):
    app: App  # set by serve()
    sweep_lock = threading.Lock()

    def log_message(self, fmt, *args) -> None:
        print(f"[{time.strftime('%H:%M:%S')}] {self.command} {self.path} {args[1]}")

    # ---- routing ----

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/alerts":
                return self._json(self._alerts_view())
            if path == "/api/settings":
                return self._json(read_editable(self.app.cfg.path))
            if path == "/api/countries":
                return self._json(
                    [{"code": c.code, "name": c.name} for c in self.app.cfg.countries.values()]
                )
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[:2] == ["api", "alerts"] and parts[3] == "events":
                return self._events_view(parts[2])
            if len(parts) == 3 and parts[0] == "api":
                api = self.app.apis.get(parts[1])
                if api is None:
                    return self._error(HTTPStatus.NOT_FOUND, "unknown country")
                until = (today() + timedelta(days=365)).isoformat()
                if parts[2] == "films":
                    return self._json(_films(api, until))
                if parts[2] == "cinemas":
                    return self._json(_cinemas(api, until, _formats(api.attributes())))
                if parts[2] == "formats":
                    return self._json(_formats(api.attributes()))
            if path.startswith("/api/"):
                return self._error(HTTPStatus.NOT_FOUND, "not found")
            self._static(path)
        except Exception as exc:  # noqa: BLE001
            self._error(HTTPStatus.BAD_GATEWAY, f"upstream error: {exc}", code="upstream", detail=str(exc))

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/notify/test":
            return self._notify_test()
        if path == "/api/run":
            return self._run_sweep()
        if path != "/api/alerts":
            return self._error(HTTPStatus.NOT_FOUND, "not found")
        try:
            payload = json.loads(self._body())
            alert = validate(payload, self.app.cfg.countries.keys(), today())
        except (ValueError, json.JSONDecodeError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, str(exc))
        try:
            self._json(self.app.alerts.add(alert), HTTPStatus.CREATED)
        except DuplicateAlert as exc:
            self._error(
                HTTPStatus.CONFLICT,
                str(exc),
                code="duplicate",
                film=exc.existing["film"]["name"],
                cinema=exc.existing["cinema"]["name"],
            )

    def do_PUT(self) -> None:
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) == 5 and parts[:2] == ["api", "alerts"] and parts[3] == "events":
            return self._set_hidden(parts[2], parts[4])
        if urlparse(self.path).path != "/api/settings":
            return self._error(HTTPStatus.NOT_FOUND, "not found")
        try:
            saved = write_editable(self.app.cfg.path, json.loads(self._body()))
            self.app.reload()
        except (ConfigError, json.JSONDecodeError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, str(exc))
        self._json(saved)

    def do_DELETE(self) -> None:
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "alerts"]:
            return self._error(HTTPStatus.NOT_FOUND, "not found")
        if not self.app.alerts.delete(parts[2]):
            return self._error(HTTPStatus.NOT_FOUND, "no such alert")
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def _notify_test(self) -> None:
        cfg = self.app.cfg
        if not cfg.ntfy_topic:
            return self._error(
                HTTPStatus.BAD_REQUEST, "no ntfy topic configured, save one first", code="no_topic"
            )
        errors = self.app.notifier.send(
            "cc-watcher test",
            f"Notifications for this topic work.\nServer: {cfg.ntfy_server}\nTopic: {cfg.ntfy_topic}",
        )
        if errors:
            return self._error(
                HTTPStatus.BAD_GATEWAY, "; ".join(errors), code="notify_failed", detail="; ".join(errors)
            )
        self._json({"ok": True, "topic": cfg.ntfy_topic})

    def _run_sweep(self) -> None:
        """One sweep on demand, same as `python src/main.py` but inside this process."""
        if not self.sweep_lock.acquire(blocking=False):
            return self._error(HTTPStatus.CONFLICT, "a sweep is already running", code="busy")
        try:
            sent = self.app.run_once()
        except Exception as exc:  # noqa: BLE001
            return self._error(HTTPStatus.INTERNAL_SERVER_ERROR, f"sweep failed: {exc}", code="run_failed", detail=str(exc))
        finally:
            self.sweep_lock.release()
        self._json({"alerts": sent})

    def _set_hidden(self, alert_id: str, event_id: str) -> None:
        try:
            hidden = bool(json.loads(self._body()).get("hidden"))
        except (json.JSONDecodeError, AttributeError):
            return self._error(HTTPStatus.BAD_REQUEST, "body must be a JSON object")
        tracked = self.app.state.load().get(alert_id, {}).get("events", {})
        if event_id not in tracked:
            return self._error(HTTPStatus.NOT_FOUND, "no such screening")
        try:
            self._json({"hiddenEvents": self.app.alerts.set_hidden(alert_id, event_id, hidden, tracked)})
        except KeyError:
            self._error(HTTPStatus.NOT_FOUND, "no such alert")

    # ---- views ----

    def _good_seats(self, ev: dict) -> bool:
        free = ev.get("current", ev.get("ratio", 0.0))
        return not ev.get("soldOut") and (1 - free) * 100 < self.app.cfg.good_seats_max_sold

    def _alerts_view(self) -> list[dict]:
        state = self.app.state.load()
        day = today().isoformat()
        out = []
        for alert in self.app.alerts.load():
            st = state.get(alert["id"], {})
            hidden = set(alert["hiddenEvents"])
            shown = {eid: ev for eid, ev in st.get("events", {}).items() if eid not in hidden}
            on_sale = st.get("on_sale")
            if on_sale is None:
                on_sale = not alert["film"].get("comingSoon")
            if alert.get("dateTo") and alert["dateTo"] < day:
                status = "expired"
            elif not on_sale:
                status = "waiting"
            elif alert.get("dateFrom") and alert["dateFrom"] > day:
                status = "upcoming"
            else:
                status = "active"
            out.append(
                {
                    **alert,
                    "status": status,
                    "onSale": on_sale,
                    "lastSweep": st.get("last_sweep"),
                    "lastAlert": st.get("last_alert"),
                    "tracked": len(shown),
                    "hidden": len(st.get("events", {})) - len(shown),
                    "goodSeats": sum(self._good_seats(ev) for ev in shown.values()),
                    "goodSeatsMaxSold": self.app.cfg.good_seats_max_sold,
                }
            )
        return out

    def _events_view(self, alert_id: str) -> None:
        alert = next((a for a in self.app.alerts.load() if a.get("id") == alert_id), None)
        if alert is None:
            return self._error(HTTPStatus.NOT_FOUND, "no such alert")
        events = self.app.state.load().get(alert_id, {}).get("events", {})
        hidden = set(alert["hiddenEvents"])
        rows = [
            {
                "id": eid,
                "when": ev.get("when"),
                "room": ev.get("room"),
                "free": ev.get("current", ev.get("ratio", 0.0)),
                "soldOut": bool(ev.get("soldOut")),
                "book": ev.get("book"),
                "hidden": eid in hidden,
                "good": eid not in hidden and self._good_seats(ev),
            }
            for eid, ev in events.items()
        ]
        rows.sort(key=lambda r: r["when"] or "")
        self._json(rows)

    # ---- plumbing ----

    def _body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length)

    def _json(self, data, status: HTTPStatus = HTTPStatus.OK) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _error(self, status: HTTPStatus, message: str, **extra) -> None:
        """`extra` carries a machine-readable code and parameters the UI can translate."""
        self._json({"error": message, **extra}, status)

    def _static(self, path: str) -> None:
        front = FRONT_DIR
        rel = "index.html" if path == "/" else path.lstrip("/")
        file = (front / rel).resolve()
        if front not in file.parents or not file.is_file():
            return self._error(HTTPStatus.NOT_FOUND, "not found")
        raw = file.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header(
            "Content-Type", mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        )
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(raw)


def serve(config_path) -> int:
    try:
        app = build(config_path)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    Handler.app = app
    sys.stdout.reconfigure(line_buffering=True)
    server = ThreadingHTTPServer((app.cfg.ui_host, app.cfg.ui_port), Handler)
    print(f"UI at http://{app.cfg.ui_host}:{app.cfg.ui_port}  (config={app.cfg.path})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cinema City watcher UI")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to the settings file")
    sys.exit(serve(parser.parse_args().config))
