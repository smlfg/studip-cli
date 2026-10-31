"""`studip news`: Ankündigungen eines Kurses oder der eigenen Kurse."""

from __future__ import annotations

from ..errors import NotFound
from ..format import format_day
from ..output import emit
from ..resolve import resolve_course
from .common import session_client


def _collect(client, kursname: str | None) -> list[dict]:
    if kursname:
        course = resolve_course(client, kursname)
        return client.course_news(course["id"])
    news: list[dict] = []
    seen: set[str] = set()
    for course in client.my_courses():
        try:
            course_news = client.course_news(course["id"])
        except NotFound:
            continue
        for item in course_news:
            key = item["id"] or f"{item['titel']}|{item['datum']}"
            if key not in seen:
                seen.add(key)
                news.append(item)
    return news


def run(json_mode: bool, kursname: str | None = None) -> int:
    with session_client() as client:
        items = _collect(client, kursname)

    items.sort(key=lambda item: str(item.get("datum") or ""), reverse=True)
    if not items:
        lines = ["Keine Ankündigungen gefunden."]
    else:
        lines = []
        for item in items:
            day = format_day(item.get("datum"))
            lines.append(f"{day}  {item['titel']}".strip())

    emit(json_mode, lines, {"news": items})
    return 0
