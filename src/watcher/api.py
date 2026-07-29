import json
import time
import urllib.request

UA = "Mozilla/5.0 (compatible; cc-watcher/0.1; personal low-volume monitor)"


class QuickbookApi:
    """Klient nieoficjalnego API repertuarowego Cinema City (data-api-service/quickbook)."""

    def __init__(self, base_url: str, lang: str, request_gap_s: float = 0.15) -> None:
        self.base_url = base_url.rstrip("/")
        self.lang = lang
        self.request_gap_s = request_gap_s
        self._last_request = 0.0

    def _get(self, path: str) -> dict:
        # minimalny odstęp między requestami — nie młócimy cudzego serwera
        wait = self._last_request + self.request_gap_s - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(
            f"{self.base_url}/{path}",
            headers={"User-Agent": UA, "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        self._last_request = time.monotonic()
        return data.get("body", {})

    def dates_with_events(self, cinema_id: str, until: str, attr: str = "") -> list[str]:
        """Dni (YYYY-MM-DD), w których kino ma jakikolwiek pasujący seans — JEDEN request.

        Pozwala pominąć dni bez seansów zamiast pytać o każdy dzień horyzontu.
        Pojawienie się nowej daty na tej liście to sam w sobie sygnał dropu.
        """
        body = self._get(f"dates/in-cinema/{cinema_id}/until/{until}?attr={attr}&lang={self.lang}")
        return body.get("dates", [])

    def film_events(self, cinema_id: str, date: str, attr: str = "") -> tuple[dict, list]:
        """Filmy (wg id) i seanse dla kina w danym dniu (YYYY-MM-DD).

        `attr` filtruje po stronie serwera. Uwaga: wiele wartości łączy się jak OR,
        więc podajemy tylko jedną (zawężenie), a resztę dociskamy po naszej stronie.
        """
        body = self._get(f"film-events/in-cinema/{cinema_id}/at-date/{date}?attr={attr}&lang={self.lang}")
        films = {f["id"]: f for f in body.get("films", [])}
        return films, body.get("events", [])
