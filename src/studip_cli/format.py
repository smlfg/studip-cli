"""Lesbare Terminalausgabe (Größen, Datum, Kurstitel)."""

from __future__ import annotations

from datetime import datetime

_UNITS = (("GB", 1024**3), ("MB", 1024**2), ("kB", 1024))


def format_size(size: object) -> str:
    """Deutsche Größenangabe, z. B. 12288 -> '12,0 kB'."""
    try:
        value = int(size)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "unbekannte Größe"
    if value < 0:
        value = 0
    if value < 1024:
        return f"{value} B"
    for unit, factor in _UNITS:
        if value >= factor:
            number = value / factor
            return f"{number:.1f}".replace(".", ",") + f" {unit}"
    return f"{value} B"


def format_course(title: str, number: str = "") -> str:
    return f"{title} ({number})" if number else title


def parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def format_day(value: object) -> str:
    parsed = parse_datetime(value)
    if parsed is None:
        return ""
    return parsed.strftime("%d.%m.%Y")


def format_event_time(start: object, end: object) -> str:
    begin = parse_datetime(start)
    finish = parse_datetime(end)
    if begin is None:
        return ""
    if finish is None:
        return begin.strftime("%d.%m.%Y %H:%M")
    if begin.date() == finish.date():
        return f"{begin.strftime('%d.%m.%Y %H:%M')}-{finish.strftime('%H:%M')}"
    return f"{begin.strftime('%d.%m.%Y %H:%M')}-{finish.strftime('%d.%m.%Y %H:%M')}"
