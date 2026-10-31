"""`studip kurse`: Kurse suchen oder eigene Kurse auflisten."""

from __future__ import annotations

from ..format import format_course
from ..output import emit
from .common import resolve_semester, session_client


def run(json_mode: bool, suchbegriff: str | None = None, semester: str | None = None) -> int:
    with session_client() as client:
        semester_id, semester_name = (
            resolve_semester(client, semester) if semester else (None, None)
        )
        if suchbegriff:
            courses = client.search_courses(
                suchbegriff, semester_id, semester_name
            )
        else:
            courses = client.my_courses(semester_id, semester_name)

    if not courses:
        lines = ["Keine Kurse gefunden."]
    else:
        lines = [
            f"{index}) {format_course(course['titel'], course['nummer'])}"
            for index, course in enumerate(courses, start=1)
        ]
    emit(json_mode, lines, {"kurse": courses})
    return 0
