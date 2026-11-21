"""Detector state machine. Run from the repository root:  pytest -q"""

import copy
from datetime import date

import pytest

from watcher.detector import Detector

DAY = date(2026, 12, 1)
FILM = {"id": "f1", "name": "Dune", "link": "https://example.test/films/dune/f1"}


class FakeApi:
    """Serves one batch of screenings per sweep; the last batch repeats."""

    def __init__(self, *batches):
        self.batches = list(batches)
        self.calls = 0

    def dates_with_events(self, cinema_id, until, attr):
        return sorted({e["eventDateTime"][:10] for e in self.batches[min(self.calls, len(self.batches) - 1)]})

    def film_events(self, cinema_id, day, attr):
        events = [e for e in self.batches[min(self.calls, len(self.batches) - 1)] if e["eventDateTime"][:10] == day]
        return {FILM["id"]: FILM}, copy.deepcopy(events)

    def next_sweep(self):
        self.calls += 1


def event(eid="e1", ratio=1.0, sold_out=False, when="2026-12-20T20:00:00", attrs=("imax",)):
    return {
        "id": eid,
        "filmId": FILM["id"],
        "eventDateTime": when,
        "auditorium": "IMAX",
        "availabilityRatio": ratio,
        "soldOut": sold_out,
        "attributeIds": list(attrs),
        "bookingLink": f"https://example.test/book/{eid}",
    }


def alert(**overrides):
    base = {
        "id": "a1",
        "film": {"id": FILM["id"], "name": FILM["name"]},
        "cinema": {"id": "c1"},
        "attrs": ["imax"],
        "dateFrom": None,
        "dateTo": None,
        "seatChanges": False,
        "hiddenEvents": [],
    }
    base.update(overrides)
    return base


def run(det, api, al, data, on_sale=frozenset({"f1"})):
    out = det.sweep(api, al, data, DAY, on_sale)
    api.next_sweep()
    return out


@pytest.fixture
def det():
    return Detector(min_ratio_delta=0.002, cooldown_min=15)


def test_first_sweep_only_records(det):
    api = FakeApi([event()])
    data = {}
    assert run(det, api, alert(), data) == []
    assert "e1" in data["events"] and data["on_sale"] is True


def test_new_screening_is_reported_after_the_first_sweep(det):
    api = FakeApi([event("e1")], [event("e1"), event("e2")])
    data = {}
    run(det, api, alert(), data)
    out = run(det, api, alert(), data)
    assert len(out) == 1 and out[0].startswith("NEW SCREENING")
    assert "https://example.test/book/e2" in out[0] and FILM["link"] in out[0]


def test_new_screening_still_fires_when_every_known_one_has_expired(det):
    """Pruning can empty the event map; that must not look like a first run."""
    api = FakeApi([event("new")])
    data = {"events": {}, "last_sweep": "2026-11-30T06:00:00+00:00"}
    assert len(run(det, api, alert(), data)) == 1


def test_film_not_on_sale_waits_then_reports_presale(det):
    api = FakeApi([event("e1"), event("e2")])
    data = {}
    assert run(det, api, alert(), data, on_sale=frozenset()) == []
    assert data["on_sale"] is False and data["events"] == {}
    out = run(det, api, alert(), data)
    assert len(out) == 2 and data["on_sale"] is True


def test_unknown_on_sale_list_scans_anyway(det):
    api = FakeApi([event()])
    data = {"events": {}, "last_sweep": "x"}
    assert len(run(det, api, alert(), data, on_sale=None)) == 1
    assert "on_sale" not in data


def test_seat_changes_off_never_reports_freed_seats(det):
    api = FakeApi([event("e1", 0.0, True), event("e2", 0.5)], [event("e1", 0.3), event("e2", 0.9)])
    data = {}
    run(det, api, alert(), data)
    assert run(det, api, alert(), data) == []


def test_seat_changes_on_merges_both_cases_into_seats_freed(det):
    api = FakeApi([event("e1", 0.0, True), event("e2", 0.5)], [event("e1", 0.3), event("e2", 0.9)])
    data = {}
    run(det, api, alert(seatChanges=True), data)
    heads = sorted(o.splitlines()[0] for o in run(det, api, alert(seatChanges=True), data))
    assert heads[0].startswith("SEATS FREED (+40.0%)")
    assert heads[1].startswith("SEATS FREED (was sold out)")


def test_cooldown_mutes_repeats_but_keeps_the_baseline(det):
    api = FakeApi([event(ratio=0.0)], [event(ratio=0.05)], [event(ratio=0.20)])
    data = {}
    al = alert(seatChanges=True)
    run(det, api, al, data)
    assert len(run(det, api, al, data)) == 1
    assert run(det, api, al, data) == []
    assert data["events"]["e1"]["ratio"] == pytest.approx(0.05)


def test_small_rises_accumulate(det):
    api = FakeApi([event(ratio=0.0)], [event(ratio=0.001)], [event(ratio=0.003)])
    data = {}
    al = alert(seatChanges=True)
    run(det, api, al, data)
    assert run(det, api, al, data) == []
    assert len(run(det, api, al, data)) == 1


def test_baseline_drops_when_seats_are_sold(det):
    api = FakeApi([event(ratio=0.5)], [event(ratio=0.0)], [event(ratio=0.02)])
    data = {}
    al = alert(seatChanges=True)
    run(det, api, al, data)
    assert run(det, api, al, data) == []
    assert len(run(det, api, al, data)) == 1


def test_hidden_screening_is_tracked_but_silent(det):
    api = FakeApi([event("e1", 0.0, True)], [event("e1", 0.5)])
    data = {}
    al = alert(seatChanges=True, hiddenEvents=["e1"])
    run(det, api, al, data)
    assert run(det, api, al, data) == []
    assert data["events"]["e1"]["current"] == 0.5


def test_date_range_and_attributes_filter_events(det):
    api = FakeApi([event("in", when="2026-12-20T20:00:00"), event("late", when="2027-01-05T20:00:00"), event("2d", attrs=("2d",))])
    data = {"events": {}, "last_sweep": "x"}
    out = run(det, api, alert(dateTo="2026-12-31"), data)
    assert len(out) == 1 and "book/in" in out[0]


def test_past_screenings_are_pruned(det):
    api = FakeApi([event("old", when="2026-11-29T20:00:00")], [])
    data = {}
    run(det, api, alert(), data)
    run(det, api, alert(), data)
    assert data["events"] == {}
