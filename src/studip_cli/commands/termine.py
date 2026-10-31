"""`studip termine`: Termine eines Kurses oder der eigenen Kurse."""

from __future__ import annotations

from ..errors import NotFound
from ..format import format_event_time
from ..output import emit
from ..resolve import resolve_course
from .common import session_client


def _collect(client, kursname: str | None) -> list[dict]:
    if kursname:
        course = resolve_course(client, kursname)
        return client.course_events(course["id"])
    events: list[dict] = []
    seen: set[str] = set()
    for course in client.my_courses():
        try:
            course_events = client.course_events(course["id"])
        except NotFound:
            continue
        for event in course_events:
            key = event["id"] or f"{event['titel']}|{event['start']}"
            if key not in seen:
                seen.add(key)
                events.append(event)
    return events


def run(json_mode: bool, kursname: str | None = None) -> int:
    with session_client() as client:
        events = _collect(client, kursname)

    events.sort(key=lambda event: str(event.get("start") or ""))
    if not events:
        lines = ["Keine Termine gefunden."]
    else:
        lines = []
        for event in events:
            when = format_event_time(event.get("start"), event.get("ende"))
            text = f"{when}  {event['titel']}".strip()
            if event.get("ort"):
                text += f" ({event['ort']})"
            lines.append(text)

    emit(json_mode, lines, {"termine": events})
    return 0
