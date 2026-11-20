"""Notification targets. The console always gets a copy; ntfy when a topic is set."""

import base64
import re
import urllib.request


class ConsoleNotifier:
    name = "console"

    def send(self, subject: str, body: str) -> None:
        print(f"\n=== {subject} ===\n{body}\n")


def _header(value: str) -> str:
    """HTTP headers are latin-1; ntfy accepts RFC 2047 encoded words for anything else."""
    try:
        value.encode("latin-1")
        return value
    except UnicodeEncodeError:
        return "=?UTF-8?B?" + base64.b64encode(value.encode("utf-8")).decode("ascii") + "?="


# ntfy turns bodies above 4096 bytes into attachments, so long ones are cut.
NTFY_BODY_LIMIT = 3800


def _fit(body: str, limit: int = NTFY_BODY_LIMIT) -> str:
    if len(body.encode("utf-8")) <= limit:
        return body
    parts = body.split("\n\n")
    kept: list[str] = []
    size = 0
    for part in parts:
        size += len(part.encode("utf-8")) + 2
        if size > limit - 40:
            break
        kept.append(part)
    return "\n\n".join(kept) + f"\n\n... and {len(parts) - len(kept)} more"


class NtfyNotifier:
    """Publishes to an ntfy topic: https://docs.ntfy.sh/publish/"""

    name = "ntfy"

    def __init__(self, server: str, topic: str, token: str = "", priority: str = "default") -> None:
        self.url = f"{server.rstrip('/')}/{topic}"
        self.token = token
        self.priority = priority

    def send(self, subject: str, body: str) -> None:
        headers = {
            "Title": _header(subject),
            "Priority": self.priority,
            "Tags": "ticket",
            "Content-Type": "text/plain; charset=utf-8",
        }
        # Tapping the notification opens the first booking link.
        link = re.search(r"book: (\S+)", body)
        if link:
            headers["Click"] = link.group(1)
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(
            self.url, data=_fit(body).encode("utf-8"), headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()


class MultiNotifier:
    """Sends to every target; one failing target does not stop the others."""

    def __init__(self, *targets) -> None:
        self.targets = targets

    def send(self, subject: str, body: str) -> list[str]:
        errors = []
        for target in self.targets:
            try:
                target.send(subject, body)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{target.name}: {exc}")
                print(f"[warn] notification via {target.name} failed: {exc}")
        return errors


def make_notifier(cfg) -> MultiNotifier:
    targets = [ConsoleNotifier()]
    if cfg.ntfy_topic:
        targets.append(NtfyNotifier(cfg.ntfy_server, cfg.ntfy_topic, cfg.ntfy_token, cfg.ntfy_priority))
    return MultiNotifier(*targets)
