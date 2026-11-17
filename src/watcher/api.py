import json
import threading
import time
import urllib.request

UA = "Mozilla/5.0 (compatible; cc-watcher/0.1; personal low-volume monitor)"


class QuickbookApi:
    """Client for the unofficial Cinema City schedule API (data-api-service/quickbook).

    The same API serves every country. Only the host, the tenant id in the base URL
    and the lang parameter differ:
        CZ  https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101  cs_CZ
        PL  https://www.cinema-city.pl/pl/data-api-service/v1/quickbook/10103  pl_PL

    Catalogue lookups (films, cinemas, attributes) are cached for `cache_s` seconds
    because the UI asks for them often. Schedule lookups are never cached.
    """

    def __init__(
        self, base_url: str, lang: str, request_gap_s: float = 0.15, cache_s: float = 0
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.lang = lang
        self.request_gap_s = request_gap_s
        self.cache_s = cache_s
        self._last_request = 0.0
        self._cache: dict[str, tuple[float, dict]] = {}
        self._lock = threading.Lock()

    def _get(self, path: str, cache: bool = False) -> dict:
        with self._lock:
            if cache:
                hit = self._cache.get(path)
                if hit and hit[0] > time.monotonic():
                    return hit[1]
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
            body = data.get("body", {})
            if cache:
                self._cache[path] = (time.monotonic() + self.cache_s, body)
            return body

    def films(self, until: str) -> list[dict]:
        """Films with at least one event up to `until` (YYYY-MM-DD)."""
        return self._get(f"films/until/{until}?attr=&lang={self.lang}", cache=True).get(
            "films", []
        )

    def cinemas(self, until: str, attr: str = "") -> list[dict]:
        """Cinemas with at least one event up to `until`, optionally filtered by attribute."""
        return self._get(
            f"cinemas/with-event/until/{until}?attr={attr}&lang={self.lang}", cache=True
        ).get("cinemas", [])

    def attributes(self) -> list[dict]:
        """Attribute catalogue as groups: [{"group-name": ..., "items": [{"id": ...}]}]."""
        return self._get(f"attributes?lang={self.lang}", cache=True).get("attributes", [])

    def dates_with_events(self, cinema_id: str, until: str, attr: str = "") -> list[str]:
        """Days (YYYY-MM-DD) on which the cinema has at least one matching event."""
        body = self._get(
            f"dates/in-cinema/{cinema_id}/until/{until}?attr={attr}&lang={self.lang}"
        )
        return body.get("dates", [])

    def film_events(self, cinema_id: str, date: str, attr: str = "") -> tuple[dict, list]:
        """Films (keyed by id) and events for a cinema on one day (YYYY-MM-DD).

        `attr` filters server-side. Several values combine with OR, so pass only
        one and filter the rest locally.
        """
        body = self._get(
            f"film-events/in-cinema/{cinema_id}/at-date/{date}?attr={attr}&lang={self.lang}"
        )
        films = {f["id"]: f for f in body.get("films", [])}
        return films, body.get("events", [])
