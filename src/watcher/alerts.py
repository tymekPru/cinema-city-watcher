"""Alert definitions: what the user wants to be told about.

alerts.json is a plain list:

    [
      {
        "id": "3f9a1c2b",
        "country": "pl",
        "film":   {"id": "7460s2r", "name": "Odyseja", "releaseDate": "2026-12-18",
                   "comingSoon": false, "poster": "https://.../7460S2R.jpg"},
        "cinema": {"id": "1060", "name": "Warszawa - Sadyba", "imax": true},
        "attrs":  ["imax", "subbed"],
        "dateFrom": "2026-11-18",      # or null: no lower bound
        "dateTo":   "2026-12-31",      # or null: no upper bound
        "seatChanges": false,          # also report seats freed on known screenings
        "hiddenEvents": ["12345"],     # screening ids the user hid; shown dimmed, never alerted
        "createdAt": "2026-11-17T21:00:00+00:00",
        "hash": "0c3b5e3a9d2f1c47"
      }
    ]

New screenings are always reported. `comingSoon` marks a film picked from the
coming-soon list before tickets were on sale; the watcher waits for it to appear.
`hash` fingerprints everything the user chose so the same alert cannot be
created twice.
"""

import hashlib
import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path


def _optional_date(value, name: str):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ValueError(f"{name} must be YYYY-MM-DD") from None


def validate(payload, country_codes, today: date) -> dict:
    """Turn a request body into a clean alert. Raises ValueError with a user-facing message."""
    if not isinstance(payload, dict):
        raise ValueError("body must be a JSON object")
    country = payload.get("country")
    if country not in country_codes:
        raise ValueError("unknown country")
    film = payload.get("film") or {}
    cinema = payload.get("cinema") or {}
    if not film.get("id") or not film.get("name"):
        raise ValueError("film is required")
    if not cinema.get("id") or not cinema.get("name"):
        raise ValueError("cinema is required")
    attrs = payload.get("attrs") or []
    if not isinstance(attrs, list) or not all(isinstance(a, str) for a in attrs):
        raise ValueError("attrs must be a list of strings")
    date_from = _optional_date(payload.get("dateFrom"), "dateFrom")
    date_to = _optional_date(payload.get("dateTo"), "dateTo")
    if date_from and date_to and date_from > date_to:
        raise ValueError("dateFrom must not be after dateTo")
    if date_to and date_to < today:
        raise ValueError("dateTo is in the past")
    release = _optional_date(film.get("releaseDate"), "film.releaseDate")
    poster = str(film.get("poster") or "")
    if poster and not poster.startswith("https://"):
        raise ValueError("film.poster must be an https URL")
    return {
        "country": country,
        "film": {
            "id": str(film["id"]),
            "name": str(film["name"]),
            "releaseDate": release.isoformat() if release else None,
            "comingSoon": bool(film.get("comingSoon")),
            "poster": poster or None,
        },
        "cinema": {
            "id": str(cinema["id"]),
            "name": str(cinema["name"]),
            "imax": bool(cinema.get("imax")),
        },
        "attrs": [a.strip() for a in attrs if a.strip()],
        "dateFrom": date_from.isoformat() if date_from else None,
        "dateTo": date_to.isoformat() if date_to else None,
        "seatChanges": bool(payload.get("seatChanges")),
    }


def fingerprint(alert: dict) -> str:
    key = {
        "country": alert["country"],
        "film": alert["film"]["id"],
        "cinema": alert["cinema"]["id"],
        "attrs": sorted(alert.get("attrs", [])),
        "dateFrom": alert.get("dateFrom"),
        "dateTo": alert.get("dateTo"),
        "seatChanges": bool(alert.get("seatChanges")),
    }
    raw = json.dumps(key, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def date_range_text(alert: dict) -> str:
    start, end = alert.get("dateFrom"), alert.get("dateTo")
    if start and end:
        return f"{start} to {end}"
    if start:
        return f"from {start}"
    if end:
        return f"until {end}"
    return "any dates"


class DuplicateAlert(ValueError):
    def __init__(self, existing: dict) -> None:
        super().__init__(
            f"an identical alert already exists: {existing['film']['name']} "
            f"at {existing['cinema']['name']} ({date_range_text(existing)})"
        )
        self.existing = existing


def _normalise(alert: dict) -> dict:
    """Fill in keys added after the alert was written and refresh its fingerprint."""
    alert.setdefault("dateFrom", None)
    alert.setdefault("dateTo", None)
    # Alerts from before this flag existed reported seat changes, so keep doing that.
    alert.setdefault("seatChanges", True)
    alert.setdefault("hiddenEvents", [])
    alert["film"].setdefault("releaseDate", None)
    alert["film"].setdefault("comingSoon", False)
    alert["film"].setdefault("poster", None)
    alert["hash"] = fingerprint(alert)
    return alert


class AlertStore:
    def __init__(self, path) -> None:
        self.path = Path(path)

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        alerts = json.loads(self.path.read_text(encoding="utf-8"))
        return [_normalise(a) for a in alerts]

    def save(self, alerts: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(alerts, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def add(self, alert: dict) -> dict:
        alert = dict(alert)
        alert["hash"] = fingerprint(alert)
        alerts = self.load()
        for existing in alerts:
            if existing["hash"] == alert["hash"]:
                raise DuplicateAlert(existing)
        alert["id"] = uuid.uuid4().hex[:8]
        alert["createdAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        alerts.append(alert)
        self.save(alerts)
        return alert

    def set_hidden(self, alert_id: str, event_id: str, hidden: bool, tracked_ids) -> list[str]:
        """Hide or unhide one screening. Ids no longer tracked are dropped on the way."""
        alerts = self.load()
        for alert in alerts:
            if alert.get("id") != alert_id:
                continue
            keep = {e for e in alert["hiddenEvents"] if e in tracked_ids}
            if hidden:
                keep.add(event_id)
            else:
                keep.discard(event_id)
            alert["hiddenEvents"] = sorted(keep)
            self.save(alerts)
            return alert["hiddenEvents"]
        raise KeyError(alert_id)

    def delete(self, alert_id: str) -> bool:
        alerts = self.load()
        kept = [a for a in alerts if a.get("id") != alert_id]
        if len(kept) == len(alerts):
            return False
        self.save(kept)
        return True
