"""Detector tests. Run from the repository root:  pytest -q"""

import copy
from datetime import datetime, timedelta

import pytest

from watcher.detector import _PRAGUE, Detector

FILM = {"id": "7268s2r", "name": "Odyssey"}


def _today():
    """Same timezone as the code under test, otherwise this is flaky around midnight."""
    return datetime.now(_PRAGUE).date()


class Cfg:
    """Minimal configuration: only the fields Detector actually reads."""

    cinema_id = "1052"
    film_id = "7268s2r"
    film_match = "odys"
    horizon_days = 7
    min_ratio_delta = 0.01
    capacity = 385
    cooldown_min = 0

    def __init__(self):
        self.required_attrs = ["70-mm"]


class FakeApi:
    """Serves one batch of screenings per sweep() call."""

    def __init__(self, batches):
        self.batches = list(batches)
        self.sweeps = 0

    def dates_with_events(self, cinema_id, until, attr):
        return [_today().isoformat()]

    def film_events(self, cinema_id, day, attr):
        events = self.batches[min(self.sweeps, len(self.batches) - 1)]
        self.sweeps += 1
        return {FILM["id"]: FILM}, copy.deepcopy(events)


class FakeState:
    """In-memory state; copies on load/save so the test never shares objects with the code."""

    def __init__(self, data=None):
        self.data = copy.deepcopy(data) if data else {}

    def load(self):
        return copy.deepcopy(self.data)

    def save(self, data):
        self.data = copy.deepcopy(data)


def event(eid="e1", ratio=0.0, days_ahead=3):
    return {
        "id": eid,
        "filmId": FILM["id"],
        "attributeIds": ["70-mm"],
        "availabilityRatio": ratio,
        "soldOut": False,
        "eventDateTime": (_today() + timedelta(days=days_ahead)).isoformat()
        + "T20:00:00",
        "auditorium": "IMAX VOLVO",
    }


def detector(batches, state=None):
    return Detector(FakeApi(batches), state or FakeState(), Cfg())


def test_first_sweep_records_state_without_alerting():
    det = detector([[event(ratio=0.05)]])

    assert det.sweep() == []
    assert det.state.data["events"]["e1"]["ratio"] == pytest.approx(0.05)


def test_new_screening_alerts_after_every_known_one_has_expired():
    """Regression: the Tuesday drop, once the previously known screenings have played.

    Pruning removes screenings that are in the past, so the event map goes empty. A sweep
    starting from that state must not be treated as a first run - otherwise the entire new
    week of screenings is absorbed silently and no mail is ever sent.
    """
    after_pruning = {"events": {}, "last_sweep": "2026-08-24T06:00:00+00:00"}
    det = detector([[event(eid="new", ratio=0.9)]], state=FakeState(after_pruning))

    alerts = det.sweep()

    assert len(alerts) == 1
    assert "NOWY SEANS" in alerts[0]
