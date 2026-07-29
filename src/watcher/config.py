import os


def _bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Config:
    """Cała konfiguracja przez zmienne środowiskowe (lokalnie i w Lambdzie)."""

    def __init__(self) -> None:
        env = os.environ.get
        self.base_url = env("CC_BASE_URL", "https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101")
        self.lang = env("CC_LANG", "cs_CZ")
        self.cinema_id = env("CINEMA_ID", "1052")            # Praha Flora (IMAX)
        self.film_id = env("FILM_ID", "")                    # np. 7268s2r; ma pierwszeństwo nad FILM_MATCH
        self.film_match = env("FILM_MATCH", "odys").lower()  # fragment nazwy filmu (case-insensitive)
        self.required_attrs = [a.strip() for a in env("REQUIRED_ATTRS", "70-mm").split(",") if a.strip()]
        self.horizon_days = int(env("HORIZON_DAYS", "45"))
        self.request_gap_s = float(env("REQUEST_GAP_S", "0.15"))
        self.min_ratio_delta = float(env("MIN_RATIO_DELTA", "0.002"))  # 1 miejsce = 1/385 ≈ 0.0026
        # 385 = wyliczona pojemność sali IMAX VOLVO (Flora); 0 = nieznana, alerty pokażą %
        self.capacity = int(env("CAPACITY", "385"))
        self.cooldown_min = int(env("ALERT_COOLDOWN_MIN", "15"))
        self.intensive = _bool("INTENSIVE", False)
        self.intensive_interval_s = float(env("INTENSIVE_INTERVAL_S", "15"))
        self.state_backend = env("STATE_BACKEND", "file")    # file | dynamodb
        self.state_file = env("STATE_FILE", "state.json")
        self.ddb_table = env("DDB_TABLE", "cc-watcher-state")
        self.notify_backend = env("NOTIFY_BACKEND", "console")  # console | ses
        self.ses_from = env("SES_FROM", "")
        self.ses_to = [a.strip() for a in env("SES_TO", "").split(",") if a.strip()]
        self.aws_region = env("WATCHER_AWS_REGION", env("AWS_REGION", "eu-central-1"))
