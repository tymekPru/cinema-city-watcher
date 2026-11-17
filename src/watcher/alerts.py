"""Alert definitions: what the user wants to be told about.

alerts.json is a plain list:

    [
      {
        "id": "3f9a1c2b",
        "country": "pl",
        "film":   {"id": "7460s2r", "name": "Odyseja"},
        "cinema": {"id": "1060", "name": "Warszawa - Sadyba", "imax": true},
        "attrs":  ["imax", "subbed"],
        "dateFrom": "2026-11-18",
        "dateTo":   "2026-12-31",
        "createdAt": "2026-11-17T21:00:00+00:00"
      }
    ]
"""

import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path


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
    try:
        date_from = date.fromisoformat(str(payload.get("dateFrom") or ""))
        date_to = date.fromisoformat(str(payload.get("dateTo") or ""))
    except ValueError:
        raise ValueError("dateFrom and dateTo must be YYYY-MM-DD") from None
    if date_from > date_to:
        raise ValueError("dateFrom must not be after dateTo")
    if date_to < today:
        raise ValueError("dateTo is in the past")
    return {
        "country": country,
        "film": {"id": str(film["id"]), "name": str(film["name"])},
        "cinema": {
            "id": str(cinema["id"]),
            "name": str(cinema["name"]),
            "imax": bool(cinema.get("imax")),
        },
        "attrs": [a.strip() for a in attrs if a.strip()],
        "dateFrom": date_from.isoformat(),
        "dateTo": date_to.isoformat(),
    }


class AlertStore:
    def __init__(self, path) -> None:
        self.path = Path(path)

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, alerts: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(alerts, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def add(self, alert: dict) -> dict:
        alert = dict(alert)
        alert["id"] = uuid.uuid4().hex[:8]
        alert["createdAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        alerts = self.load()
        alerts.append(alert)
        self.save(alerts)
        return alert

    def delete(self, alert_id: str) -> bool:
        alerts = self.load()
        kept = [a for a in alerts if a.get("id") != alert_id]
        if len(kept) == len(alerts):
            return False
        self.save(kept)
        return True
