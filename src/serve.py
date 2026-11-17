"""Web UI for managing alerts.

    python src/serve.py [--config PATH]

Serves the static front-end from front/ and a small JSON API on top of the same
settings and data files the watcher uses. Standard library only.
"""

import argparse
import json
import mimetypes
import sys
import time
from datetime import timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from watcher.alerts import validate
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
    }


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
                    return self._json([_film_view(f) for f in api.films(until)])
                if parts[2] == "cinemas":
                    imax = {c["id"] for c in api.cinemas(until, "imax")}
                    return self._json(
                        [
                            {"id": c["id"], "name": c["displayName"], "imax": c["id"] in imax}
                            for c in api.cinemas(until)
                        ]
                    )
                if parts[2] == "formats":
                    return self._json(_formats(api.attributes()))
            if path.startswith("/api/"):
                return self._error(HTTPStatus.NOT_FOUND, "not found")
            self._static(path)
        except Exception as exc:  # noqa: BLE001
            self._error(HTTPStatus.BAD_GATEWAY, f"upstream error: {exc}")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/alerts":
            return self._error(HTTPStatus.NOT_FOUND, "not found")
        try:
            payload = json.loads(self._body())
            alert = validate(payload, self.app.cfg.countries.keys(), today())
        except (ValueError, json.JSONDecodeError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, str(exc))
        self._json(self.app.alerts.add(alert), HTTPStatus.CREATED)

    def do_PUT(self) -> None:
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

    # ---- views ----

    def _alerts_view(self) -> list[dict]:
        state = self.app.state.load()
        day = today().isoformat()
        out = []
        for alert in self.app.alerts.load():
            st = state.get(alert["id"], {})
            if alert["dateTo"] < day:
                status = "expired"
            elif alert["dateFrom"] > day:
                status = "upcoming"
            else:
                status = "active"
            out.append(
                {
                    **alert,
                    "status": status,
                    "lastSweep": st.get("last_sweep"),
                    "lastAlert": st.get("last_alert"),
                    "tracked": len(st.get("events", {})),
                }
            )
        return out

    def _events_view(self, alert_id: str) -> None:
        if not any(a.get("id") == alert_id for a in self.app.alerts.load()):
            return self._error(HTTPStatus.NOT_FOUND, "no such alert")
        events = self.app.state.load().get(alert_id, {}).get("events", {})
        rows = [
            {
                "id": eid,
                "when": ev.get("when"),
                "room": ev.get("room"),
                "free": ev.get("current", ev.get("ratio", 0.0)),
                "soldOut": bool(ev.get("soldOut")),
                "book": ev.get("book"),
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

    def _error(self, status: HTTPStatus, message: str) -> None:
        self._json({"error": message}, status)

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
