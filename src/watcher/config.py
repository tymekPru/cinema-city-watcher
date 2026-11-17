import json
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


# Settings the UI may change, with the type each value is coerced to.
EDITABLE = {
    "api.requestGapSeconds": float,
    "api.cacheSeconds": float,
    "alerts.minRatioDelta": float,
    "alerts.cooldownMinutes": int,
    "runtime.pollIntervalSeconds": float,
    "runtime.dataDir": str,
}


def read_editable(path) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out: dict = {}
    for dotted in EDITABLE:
        section, key = dotted.split(".")
        out.setdefault(section, {})[key] = _require(raw, dotted)
    return out


def write_editable(path, patch: dict) -> dict:
    """Validate `patch` (shaped like appsettings.json) and merge it into the file."""
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(patch, dict):
        raise ConfigError("body must be a JSON object")
    for dotted, typ in EDITABLE.items():
        section, key = dotted.split(".")
        if not isinstance(patch.get(section), dict) or key not in patch[section]:
            continue
        value = patch[section][key]
        try:
            value = typ(value)
        except (TypeError, ValueError):
            kind = {int: "an integer", float: "a number", str: "text"}[typ]
            raise ConfigError(f"{dotted} must be {kind}") from None
        if typ is str and not value.strip():
            raise ConfigError(f"{dotted} must not be empty")
        if typ is not str and value < 0:
            raise ConfigError(f"{dotted} must not be negative")
        if dotted == "runtime.pollIntervalSeconds" and value < 1:
            raise ConfigError(f"{dotted} must be at least 1")
        raw.setdefault(section, {})[key] = value
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return read_editable(path)
