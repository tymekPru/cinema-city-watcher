"""Compare the current schedule against remembered state and produce alerts.

The API only reports what is on sale right now, so every useful signal (a new
screening, seats coming back) is a change between two sweeps. The state file is
that memory, one entry per alert id:

    {
      "<alert id>": {
        "events": {
          "<event id>": {
            "ratio":   0.12,      # baseline free-seat ratio used for comparison
            "current": 0.15,      # free-seat ratio as of the last sweep (for the UI)
            "soldOut": false,
            "when":    "2026-09-02T20:00:00",
            "room":    "IMAX",
            "book":    "<booking link>",
            "seen":    "<first time this event was seen>",
            "alerts":  {"NEW SEATS": "<last time this kind was sent>"}
          }
        },
        "last_sweep": "<end of the last completed sweep>",
        "last_alert": "<last time this alert produced a notification>"
      }
    }

Alert kinds:
    NEW SCREENING   a matching event not seen before
    TICKETS BACK    the event was sold out and no longer is
    NEW SEATS       free-seat ratio rose by at least min_ratio_delta above the baseline

Rules:
    1. The first sweep only records state and sends nothing. "First" means there is
       no last_sweep yet, not that events is empty, because rule 4 can empty events.
    2. The same alert kind for the same event is not repeated within cooldown_min.
    3. The baseline rises only when an alert is actually sent, and falls as soon as
       seats are sold. Otherwise a rise muted by the cooldown, or one too small on
       its own, would be forgotten and seats trickling back would never add up.
    4. Events that have already played are dropped so the state does not grow.

min_ratio_delta also hides permanently free seats (wheelchair spaces, restricted
view), which sit at a constant ratio.
"""

from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    # Czechia and Poland share this zone. It decides which calendar day "today" is.
    LOCAL_TZ = ZoneInfo("Europe/Prague")
except (ImportError, KeyError):
    # No zoneinfo or no tzdata installed. UTC only differs around midnight.
    LOCAL_TZ = timezone.utc


def today() -> date:
    return datetime.now(LOCAL_TZ).date()


class Detector:
    def __init__(self, min_ratio_delta: float, cooldown_min: int) -> None:
        self.min_ratio_delta = min_ratio_delta
        self.cooldown_min = cooldown_min

    def sweep(self, api, alert: dict, data: dict, day: date) -> list[str]:
        """One sweep for one alert. `data` is that alert's state, updated in place."""
        known = data.setdefault("events", {})
        first_run = "last_sweep" not in data
        cinema_id = alert["cinema"]["id"]
        film_id = alert["film"]["id"]
        attrs = set(alert["attrs"])
        # The API combines several attributes with OR, so only one is sent
        # server-side; the rest are checked locally.
        server_attr = alert["attrs"][0] if alert["attrs"] else ""
        start = max(day.isoformat(), alert["dateFrom"])
        end = alert["dateTo"]
        texts: list[str] = []

        for d in self._dates_to_scan(api, cinema_id, start, end, server_attr):
            try:
                films, events = api.film_events(cinema_id, d, server_attr)
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] {alert['id']} {d}: {exc}")
                continue
            for ev in events:
                if ev.get("filmId") != film_id:
                    continue
                if not attrs <= set(ev.get("attributeIds", [])):
                    continue
                text = self._check_event(ev, films.get(film_id, {}), known, first_run)
                if text:
                    texts.append(text)

        cutoff = (day - timedelta(days=1)).isoformat()
        for eid in [k for k, v in known.items() if (v.get("when") or "9999")[:10] < cutoff]:
            del known[eid]

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        data["last_sweep"] = now
        if texts:
            data["last_alert"] = now
        if first_run:
            print(f"[init] {alert['id']}: tracking {len(known)} screenings, no alerts sent")
        return texts

    def _dates_to_scan(self, api, cinema_id, start, end, attr) -> list[str]:
        try:
            return [d for d in api.dates_with_events(cinema_id, end, attr) if start <= d <= end]
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] date list unavailable, scanning every day: {exc}")
        first = date.fromisoformat(start)
        days = (date.fromisoformat(end) - first).days
        return [(first + timedelta(days=o)).isoformat() for o in range(days + 1)]

    def _check_event(self, ev: dict, film: dict, known: dict, first_run: bool):
        eid = str(ev["id"])
        ratio = float(ev.get("availabilityRatio") or 0.0)
        sold_out = bool(ev.get("soldOut"))
        now = datetime.now(timezone.utc)
        prev = known.get(eid)
        prev_ratio = float((prev or {}).get("ratio") or 0.0)
        rec = known[eid] = {
            # Baseline moves down immediately, up only when an alert is sent below.
            "ratio": ratio if prev is None else min(prev_ratio, ratio),
            "current": ratio,
            "soldOut": sold_out,
            "when": ev.get("eventDateTime"),
            "room": ev.get("auditorium"),
            "book": ev.get("bookingRouterLaunchLink") or ev.get("bookingLink"),
            "seen": (prev or {}).get("seen") or now.isoformat(timespec="seconds"),
            "alerts": (prev or {}).get("alerts", {}),
        }

        if prev is None:
            if first_run:
                return None
            kind, extra = "NEW SCREENING", ""
        elif prev.get("soldOut") and not sold_out and ratio >= self.min_ratio_delta:
            kind, extra = "TICKETS BACK", ""
        elif ratio - prev_ratio >= self.min_ratio_delta:
            kind, extra = "NEW SEATS", f" (+{ratio - prev_ratio:.1%})"
        else:
            return None

        if not self._cooldown_ok(rec, kind, now):
            return None
        rec["ratio"] = ratio
        rec["alerts"][kind] = now.isoformat(timespec="seconds")

        when = (ev.get("eventDateTime") or "")[:16].replace("T", " ")
        lines = [
            f"{kind}{extra}: {film.get('name', '?')} | {when}"
            f" | {ev.get('auditorium', '?')} | free ~{ratio:.1%}"
        ]
        if rec["book"]:
            lines.append(f"  book: {rec['book']}")
        if film.get("link"):
            lines.append(f"  film: {film['link']}")
        return "\n".join(lines)

    def _cooldown_ok(self, rec: dict, kind: str, now: datetime) -> bool:
        last = rec["alerts"].get(kind)
        if not last:
            return True
        return now - datetime.fromisoformat(last) >= timedelta(minutes=self.cooldown_min)
