"""Alert validation, fingerprints and the store."""

from datetime import date

import pytest

from watcher.alerts import AlertStore, DuplicateAlert, fingerprint, validate

TODAY = date(2026, 12, 1)
COUNTRIES = {"cz", "pl"}


def payload(**overrides):
    base = {
        "country": "pl",
        "film": {"id": "f1", "name": "Dune", "releaseDate": "2026-12-18", "comingSoon": False},
        "cinema": {"id": "1060", "name": "Sadyba", "imax": True},
        "attrs": ["imax", "subbed"],
        "dateFrom": None,
        "dateTo": None,
        "seatChanges": False,
    }
    base.update(overrides)
    return base


def test_validate_accepts_open_dates_and_normalises():
    alert = validate(payload(), COUNTRIES, TODAY)
    assert alert["dateFrom"] is None and alert["dateTo"] is None
    assert alert["seatChanges"] is False and alert["film"]["poster"] is None


@pytest.mark.parametrize(
    "bad, message",
    [
        ({"country": "de"}, "unknown country"),
        ({"film": {}}, "film is required"),
        ({"dateFrom": "2026-12-31", "dateTo": "2026-12-01"}, "dateFrom must not be after dateTo"),
        ({"dateTo": "2026-11-01"}, "dateTo is in the past"),
        ({"dateFrom": "31/12/2026"}, "dateFrom must be YYYY-MM-DD"),
        ({"film": {"id": "f1", "name": "x", "poster": "http://plain"}}, "film.poster must be an https URL"),
    ],
)
def test_validate_rejects(bad, message):
    with pytest.raises(ValueError, match=message):
        validate(payload(**bad), COUNTRIES, TODAY)


def test_fingerprint_covers_user_choices_only():
    a = validate(payload(), COUNTRIES, TODAY)
    same = validate(payload(attrs=["subbed", "imax"], film={"id": "f1", "name": "Other name"}), COUNTRIES, TODAY)
    assert fingerprint(a) == fingerprint(same)
    assert fingerprint(a) != fingerprint(validate(payload(seatChanges=True), COUNTRIES, TODAY))
    assert fingerprint(a) != fingerprint(validate(payload(dateTo="2026-12-31"), COUNTRIES, TODAY))


def test_store_rejects_duplicates_and_assigns_ids(tmp_path):
    store = AlertStore(tmp_path / "alerts.json")
    first = store.add(validate(payload(), COUNTRIES, TODAY))
    assert len(first["id"]) == 8 and first["createdAt"]
    with pytest.raises(DuplicateAlert, match="any dates"):
        store.add(validate(payload(), COUNTRIES, TODAY))
    store.add(validate(payload(seatChanges=True), COUNTRIES, TODAY))
    assert len(store.load()) == 2


def test_load_backfills_old_alerts(tmp_path):
    path = tmp_path / "alerts.json"
    path.write_text('[{"id":"old","country":"cz","film":{"id":"f","name":"F"},"cinema":{"id":"1","name":"C"},"attrs":[],"dateFrom":"2026-12-01","dateTo":"2026-12-31"}]')
    (alert,) = AlertStore(path).load()
    assert alert["seatChanges"] is True and alert["hiddenEvents"] == [] and alert["hash"]


def test_update_keeps_state_for_same_target_and_resets_otherwise(tmp_path):
    store = AlertStore(tmp_path / "alerts.json")
    saved = store.add(validate(payload(), COUNTRIES, TODAY))
    store.set_hidden(saved["id"], "e1", True, {"e1"})

    same, reset = store.update(saved["id"], validate(payload(dateTo="2026-12-31"), COUNTRIES, TODAY))
    assert reset is False and same["hiddenEvents"] == ["e1"] and same["id"] == saved["id"]

    other, reset = store.update(saved["id"], validate(payload(attrs=["imax"]), COUNTRIES, TODAY))
    assert reset is True and other["hiddenEvents"] == []

    store.add(validate(payload(seatChanges=True), COUNTRIES, TODAY))
    with pytest.raises(DuplicateAlert):
        store.update(saved["id"], validate(payload(seatChanges=True), COUNTRIES, TODAY))
    with pytest.raises(KeyError):
        store.update("nope", validate(payload(), COUNTRIES, TODAY))


def test_set_hidden_prunes_stale_ids(tmp_path):
    store = AlertStore(tmp_path / "alerts.json")
    saved = store.add(validate(payload(), COUNTRIES, TODAY))
    assert store.set_hidden(saved["id"], "e1", True, {"e1", "e2"}) == ["e1"]
    assert store.set_hidden(saved["id"], "e2", True, {"e2"}) == ["e2"]
    assert store.set_hidden(saved["id"], "e2", False, {"e2"}) == []
