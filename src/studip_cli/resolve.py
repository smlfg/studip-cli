"""Kurs- und Dateiauflösung über Namen statt IDs."""

from __future__ import annotations

import sys

from .client import Client
from .errors import NotFound, UsageError
from .format import format_course
from .ui import choose


def _label(course: dict) -> str:
    return format_course(course.get("titel", ""), course.get("nummer", ""))


def resolve_course(client: Client, name: str) -> dict:
    query = (name or "").strip()
    if not query:
        raise UsageError("Kursname fehlt", "studip kurse <suchbegriff> ausführen")
    courses = client.search_courses(query)
    if not courses:
        raise NotFound(
            f"Kein Kurs gefunden: {query}",
            "Suchbegriff prüfen oder studip kurse <begriff> ausführen",
        )
    exact = [
        course for course in courses if course["titel"].casefold() == query.casefold()
    ]
    if len(exact) == 1:
        return exact[0]
    if len(courses) == 1:
        return courses[0]
    if sys.stdin.isatty() and sys.stdout.isatty():
        return choose(courses, _label, "Kurse")
    for index, course in enumerate(courses, start=1):
        sys.stderr.write(f"{index}) {_label(course)}\n")
    sys.stderr.flush()
    raise UsageError(
        f"Mehrere Kurse gefunden: {query}",
        "Eindeutigeren Kursnamen angeben",
    )


def resolve_course_files(files: list[dict], name: str) -> list[dict]:
    query = (name or "").strip()
    exact = [item for item in files if item["name"].casefold() == query.casefold()]
    if len(exact) == 1:
        return exact
    if len(exact) > 1:
        candidates = exact
    else:
        candidates = [
            item for item in files if query.casefold() in item["name"].casefold()
        ]
    if not candidates:
        raise NotFound(
            f"Keine Datei gefunden: {query}",
            "Dateinamen prüfen oder studip dateien <kursname> ausführen",
        )
    if len(candidates) == 1:
        return candidates
    if sys.stdin.isatty() and sys.stdout.isatty():
        return [choose(candidates, lambda item: item["name"], "Dateien")]
    for index, item in enumerate(candidates, start=1):
        sys.stderr.write(f"{index}) {item['name']}\n")
    sys.stderr.flush()
    raise UsageError(
        f"Mehrere Dateien gefunden: {query}",
        "Eindeutigeren Dateinamen angeben",
    )
