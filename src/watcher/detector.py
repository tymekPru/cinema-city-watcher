"""Turns the cinema's current schedule into alerts worth mailing.

WHY THIS IS NOT A DIFF OF TWO LISTS
-----------------------------------
The API only ever answers "here is what is on sale right now". Everything interesting -
a screening appearing, seats coming back - is a *change*, so the watcher has to remember
what it saw last time and compare. That memory is the state, and every subtlety in this
module comes from keeping it honest.

STATE
-----
One dictionary, persisted between runs (a local file, or DynamoDB on AWS)::

    {
      "events": {
        "<screening id>": {
          "ratio":   0.12,          # comparison baseline, NOT simply "last seen value"
          "soldOut": False,
          "when":    "2026-09-02T20:00:00",
          "seen":    "<first time we saw this screening>",
          "alerts":  {"NOWE MIEJSCA": "<when we last mailed about this kind>"},
        },
      },
      "last_sweep": "<end of the last completed sweep>",
    }

ONE SWEEP
---------
Ask the API which days have matching screenings, fetch each day, keep the ones that pass
the film and attribute filters, and compare every screening against its remembered record.
The sweep returns alert texts; mailing them is the caller's job (see runner.py).

THREE KINDS OF ALERT
--------------------
NOWY SEANS      a matching screening we have never seen before (the weekly drop)
POWROT BILETOW  it was soldOut, and now it is not
NOWE MIEJSCA    the free-seat ratio rose by at least ``min_ratio_delta`` above the baseline

FOUR RULES THAT KEEP THE MAILBOX USABLE - AND WHY EACH EXISTS
-------------------------------------------------------------
1. First sweep stays silent. Without it the very first mail would list every screening in
   the horizon. "First" is decided by the absence of ``last_sweep`` - deliberately not by
   an empty ``events`` map, because rule 4 can empty that map at any time.

2. Cooldown. The same kind of alert for the same screening is not repeated more often than
   ``cooldown_min``, so a screening hovering around the threshold cannot mail every minute.

3. The baseline only rises when an alert is actually sent, and falls as soon as seats are
   sold. If it simply followed the last observed value, a rise muted by rule 2 would be
   forgotten, and seats trickling back a few at a time would never add up to an alert.

4. Screenings that have already played are dropped from the state, so it does not grow
   forever. This is what can empty ``events`` - hence the wording of rule 1.

Threshold ``min_ratio_delta`` also does quiet work: a handful of permanently free seats
(wheelchair spaces, restricted view) sit at a constant ratio and never trigger anything.
"""

from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    _PRAGUE = ZoneInfo("Europe/Prague")
except Exception:  # brak tzdata — UTC wystarczy, różnica dotyka tylko okolic północy
    _PRAGUE = timezone.utc

BOOKING_LINK = "https://www.cinemacity.cz/cz/booking-router/launch/{event_id}?lang=cs"


class Detector:
    """Porównuje bieżący repertuar z zapamiętanym stanem i produkuje alerty.

    Trzy sygnały:
      NOWY SEANS   — pojawił się pasujący seans, którego nie znaliśmy (środowy drop)
      POWRÓT       — seans był soldOut, a już nie jest
      NOWE MIEJSCA — availabilityRatio wzrósł o >= min_ratio_delta względem
                     ostatniego stanu; dzięki liczeniu od baseline'u wiecznie
                     wolne miejsca (np. dla wózków) nie generują fałszywych alarmów
    """

    def __init__(self, api, state, cfg) -> None:
        self.api = api
        self.state = state
        self.cfg = cfg

    # ---- filtry ----

    def _film_ok(self, film: dict) -> bool:
        if self.cfg.film_id:
            return film.get("id") == self.cfg.film_id
        return self.cfg.film_match in film.get("name", "").lower()

    def _attrs_ok(self, event: dict) -> bool:
        attrs = set(event.get("attributeIds", []))
        return all(a in attrs for a in self.cfg.required_attrs)

    # ---- główny cykl ----

    def _dates_to_scan(self, today) -> list[str]:
        """Dni do odpytania: najpierw pytamy API, które w ogóle mają pasujące seanse."""
        until = (today + timedelta(days=self.cfg.horizon_days)).isoformat()
        try:
            dates = self.api.dates_with_events(self.cfg.cinema_id, until, self._server_attr())
            if dates:
                return [d for d in dates if d >= today.isoformat()]
        except Exception as exc:
            print(f"[warn] lista dat niedostępna, skanuję cały horyzont: {exc}")
        return [(today + timedelta(days=o)).isoformat() for o in range(self.cfg.horizon_days + 1)]

    def _server_attr(self) -> str:
        # tylko jeden atrybut serwerowo — wiele wartości działa jak OR i rozszerzyłoby wynik
        return self.cfg.required_attrs[0] if self.cfg.required_attrs else ""

    def sweep(self) -> list[str]:
        """Jeden przebieg po dniach z seansami. Zwraca listę alertów (tekstów)."""
        data = self.state.load()
        known = data.setdefault("events", {})
        first_run = "last_sweep" not in data
        alerts: list[str] = []
        today = datetime.now(_PRAGUE).date()

        for date in self._dates_to_scan(today):
            try:
                films, events = self.api.film_events(self.cfg.cinema_id, date, self._server_attr())
            except Exception as exc:  # jeden feralny dzień nie ubija całego przebiegu
                print(f"[warn] {date}: {exc}")
                continue
            for ev in events:
                film = films.get(ev.get("filmId"), {})
                if not self._film_ok(film) or not self._attrs_ok(ev):
                    continue
                alert = self._check_event(ev, film, known, first_run)
                if alert:
                    alerts.append(alert)

        # sprzątanie: seanse, które już się odbyły
        cutoff = (today - timedelta(days=1)).isoformat()
        for eid in [k for k, v in known.items() if (v.get("when") or "9999")[:10] < cutoff]:
            del known[eid]

        data["last_sweep"] = datetime.now(timezone.utc).isoformat()
        self.state.save(data)
        if first_run:
            print(f"[init] zainicjalizowano stan: {len(known)} pasujących seansów (bez alertów)")
        return alerts

    def _check_event(self, ev: dict, film: dict, known: dict, first_run: bool):
        eid = str(ev["id"])
        ratio = float(ev.get("availabilityRatio") or 0.0)
        sold_out = bool(ev.get("soldOut"))
        now = datetime.now(timezone.utc)
        prev = known.get(eid)
        prev_ratio = float((prev or {}).get("ratio") or 0.0)
        known[eid] = {
            # Comparison baseline for the next sweep. It only moves UP when an alert is
            # actually sent (see the end of this method); otherwise a rise swallowed by the
            # cooldown - or one too small to alert on its own - would be forgotten. It moves
            # DOWN as soon as seats are sold, so tickets coming back are still noticed.
            "ratio": ratio if prev is None else min(prev_ratio, ratio),
            "soldOut": sold_out,
            "when": ev.get("eventDateTime"),
            "seen": (prev or {}).get("seen") or now.isoformat(),
            "alerts": (prev or {}).get("alerts", {}),
        }
        rec = known[eid]

        if prev is None:
            if first_run:
                return None
            kind, extra = "NOWY SEANS", ""
        elif prev.get("soldOut") and not sold_out and ratio >= self.cfg.min_ratio_delta:
            kind, extra = "POWRÓT BILETÓW", ""
        elif ratio - prev_ratio >= self.cfg.min_ratio_delta:
            kind, extra = "NOWE MIEJSCA", f" (+{self._seats(ratio - prev_ratio)})"
        else:
            return None

        if not self._cooldown_ok(rec, kind, now):
            return None
        rec["ratio"] = ratio
        rec["alerts"][kind] = now.isoformat()
        when = (ev.get("eventDateTime") or "")[:16].replace("T", " ")
        return (
            f"{kind}{extra}: {film.get('name', '?')} — {when}"
            f" | sala {ev.get('auditorium', '?')} | wolne ~{self._seats(ratio)}"
            f"\n  kup: {BOOKING_LINK.format(event_id=eid)}"
        )

    def _seats(self, ratio: float) -> str:
        if self.cfg.capacity:
            return f"{max(1, round(ratio * self.cfg.capacity))} miejsc"
        return f"{ratio:.1%}"

    def _cooldown_ok(self, rec: dict, kind: str, now: datetime) -> bool:
        last = rec["alerts"].get(kind)
        if not last:
            return True
        return now - datetime.fromisoformat(last) >= timedelta(minutes=self.cfg.cooldown_min)
