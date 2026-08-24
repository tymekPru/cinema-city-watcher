"""Testy detektora. Uruchomienie z katalogu repo:  pytest -q"""

import copy
from datetime import datetime, timedelta

import pytest

from watcher.detector import _PRAGUE, Detector

FILM = {"id": "7268s2r", "name": "Odyseja"}


def _today():
    """Ta sama strefa co w kodzie — inaczej test bywa flaky w okolicach polnocy."""
    return datetime.now(_PRAGUE).date()


class Cfg:
    """Minimalna konfiguracja — tylko pola, ktorych uzywa Detector."""

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
    """Oddaje kolejne partie seansow — jedna partia na jeden sweep()."""

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
    """Stan w pamieci; kopiuje przy load/save, zeby test nie dzielil obiektow z kodem."""

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


def test_pierwszy_przebieg_zapamietuje_bez_alertow():
    det = detector([[event(ratio=0.05)]])

    assert det.sweep() == []
    assert det.state.data["events"]["e1"]["ratio"] == pytest.approx(0.05)


def test_nowy_seans_po_wygasnieciu_wszystkich_znanych_daje_alert():
    """Regresja: wtorkowy drop po tym, jak stare seanse sie odbyly.

    Sprzatanie usuwa z pamieci seanse z przeszlosci, wiec mapa zdarzen robi sie
    pusta. Detektor NIE moze uznac takiego przebiegu za pierwszy — inaczej caly
    nowy tydzien wchodzi po cichu i nie leci zaden mail.
    """
    po_sprzataniu = {"events": {}, "last_sweep": "2026-08-24T06:00:00+00:00"}
    det = detector([[event(eid="nowy", ratio=0.9)]], state=FakeState(po_sprzataniu))

    alerty = det.sweep()

    assert len(alerty) == 1
    assert "NOWY SEANS" in alerty[0]
