"""Gemeinsame Helfer für die Unterkommandos."""

from __future__ import annotations

from ..client import Client
from ..config import resolve_credentials
from ..errors import SourceError


def session_client() -> Client:
    credentials = resolve_credentials()
    assert credentials is not None
    base_url, user, password = credentials
    return Client(base_url, user, password)


def resolve_semester(client: Client, value: str) -> str:
    """Liefert die Semester-ID zu Name oder ID; unbekannt ist ein Quellenfehler."""
    text = value.strip()
    if not text:
        raise SourceError("Leerer Semesterwert", "Semestername oder ID angeben")
    try:
        semesters = client.semesters()
    except SourceError:
        return text
    for semester in semesters:
        if semester["id"] == text or semester["name"].casefold() == text.casefold():
            return semester["id"]
    raise SourceError(
        f"Unbekanntes Semester: {text}",
        "Semestername prüfen oder ohne --semester aufrufen",
    )
