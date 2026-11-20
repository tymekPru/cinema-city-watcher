import json
import re
from pathlib import Path


class ConfigError(Exception):
    pass


def _require(raw: dict, dotted: str):
    node = raw
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise ConfigError(f"missing setting: {dotted}")
        node = node[part]
    return node


class Country:
    def __init__(self, code: str, raw: dict) -> None:
        self.code = code
        self.name = str(raw.get("name", code.upper()))
        self.base_url = str(raw["baseUrl"]).rstrip("/")
        self.lang = str(raw["lang"])


class Config:
    """Settings loaded from appsettings.json. Every key is required."""

    def __init__(self, path) -> None:
        self.path = Path(path).resolve()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise ConfigError(f"settings file not found: {self.path}") from None
        except json.JSONDecodeError as exc:
            raise ConfigError(f"{self.path}: invalid JSON: {exc}") from None

        countries = _require(raw, "countries")
        if not isinstance(countries, dict) or not countries:
            raise ConfigError("countries must be a non-empty object")
        self.countries: dict[str, Country] = {}
        for code, c in countries.items():
            for key in ("baseUrl", "lang"):
                if not isinstance(c, dict) or key not in c:
                    raise ConfigError(f"missing setting: countries.{code}.{key}")
            self.countries[code] = Country(code, c)

        self.request_gap_s = float(_require(raw, "api.requestGapSeconds"))
        self.cache_s = float(_require(raw, "api.cacheSeconds"))

        self.min_ratio_delta = float(_require(raw, "alerts.minRatioDelta"))
        self.cooldown_min = int(_require(raw, "alerts.cooldownMinutes"))

        self.poll_interval_s = float(_require(raw, "runtime.pollIntervalSeconds"))
        data_dir = Path(str(_require(raw, "runtime.dataDir")))
        # Relative paths resolve next to the settings file, so cron can run from anywhere.
        self.data_dir = data_dir if data_dir.is_absolute() else self.path.parent / data_dir
        self.alerts_file = self.data_dir / "alerts.json"
        self.state_file = self.data_dir / "state.json"

        self.ui_host = str(_require(raw, "ui.host"))
        self.ui_port = int(_require(raw, "ui.port"))

        self.ntfy_server = str(_require(raw, "notify.ntfy.server")).rstrip("/")
        self.ntfy_topic = str(_require(raw, "notify.ntfy.topic")).strip()
        self.ntfy_token = str(_require(raw, "notify.ntfy.token")).strip()
        self.ntfy_priority = str(_require(raw, "notify.ntfy.priority")).strip() or "default"


NTFY_PRIORITIES = ("min", "low", "default", "high", "urgent")

# Settings the UI may change, with the type each value is coerced to.
EDITABLE = {
    "api.requestGapSeconds": float,
    "api.cacheSeconds": float,
    "alerts.minRatioDelta": float,
    "alerts.cooldownMinutes": int,
    "runtime.pollIntervalSeconds": float,
    "runtime.dataDir": str,
    "notify.ntfy.server": str,
    "notify.ntfy.topic": str,
    "notify.ntfy.token": str,
    "notify.ntfy.priority": str,
}
# Keys that may be left empty.
OPTIONAL = {"notify.ntfy.topic", "notify.ntfy.token"}


def _set(raw: dict, dotted: str, value) -> None:
    node = raw
    parts = dotted.split(".")
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def _lookup(raw: dict, dotted: str):
    """Like _require but returns None when the key is absent."""
    node = raw
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _check(dotted: str, value) -> None:
    if dotted == "runtime.pollIntervalSeconds" and value < 1:
        raise ConfigError(f"{dotted} must be at least 1")
    if dotted == "notify.ntfy.server" and not re.match(r"^https?://[^/\s]+", value):
        raise ConfigError(f"{dotted} must be an http(s) URL")
    if dotted == "notify.ntfy.topic" and value and not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise ConfigError(f"{dotted} may only contain letters, digits, - and _ (max 64)")
    if dotted == "notify.ntfy.priority" and value not in NTFY_PRIORITIES:
        raise ConfigError(f"{dotted} must be one of {', '.join(NTFY_PRIORITIES)}")


def read_editable(path) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out: dict = {}
    for dotted in EDITABLE:
        _set(out, dotted, _require(raw, dotted))
    return out


def write_editable(path, patch: dict) -> dict:
    """Validate `patch` (shaped like appsettings.json) and merge it into the file."""
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(patch, dict):
        raise ConfigError("body must be a JSON object")
    for dotted, typ in EDITABLE.items():
        value = _lookup(patch, dotted)
        if value is None:
            continue
        try:
            value = typ(value)
        except (TypeError, ValueError):
            kind = {int: "an integer", float: "a number", str: "text"}[typ]
            raise ConfigError(f"{dotted} must be {kind}") from None
        if typ is str:
            value = value.strip()
            if not value and dotted not in OPTIONAL:
                raise ConfigError(f"{dotted} must not be empty")
        elif value < 0:
            raise ConfigError(f"{dotted} must not be negative")
        _check(dotted, value)
        _set(raw, dotted, value)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return read_editable(path)
