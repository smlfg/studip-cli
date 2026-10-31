"""Client für die Stud.IP-JSON:API und Parser für JSON:API-Antworten."""

from __future__ import annotations

from typing import Any

import httpx

from . import __version__
from .config import normalize_base_url
from .errors import LoginFailed, LoginRequired, NetworkError, NotFound, SourceError

API = "/jsonapi.php/v1"
ACCEPT = "application/vnd.api+json"


def _attr(item: dict, *names: str, default: Any = None) -> Any:
    attributes = item.get("attributes") or {}
    for name in names:
        value = attributes.get(name)
        if value not in (None, ""):
            return value
    return default


def _items(payload: Any) -> list[dict]:
    if not isinstance(payload, dict):
        raise SourceError("Unerwartete Antwort der Stud.IP-Schnittstelle")
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0] if isinstance(errors[0], dict) else {}
        detail = first.get("detail") or first.get("title") or "Unbekannter Fehler"
        raise SourceError(f"Stud.IP meldet: {detail}")
    return []


def _relationship_id(item: dict, name: str) -> str | None:
    relationship = (item.get("relationships") or {}).get(name) or {}
    data = relationship.get("data")
    if isinstance(data, dict):
        value = data.get("id")
        return str(value) if value is not None else None
    return None


def parse_course(item: dict) -> dict:
    return {
        "id": str(item.get("id", "")),
        "titel": str(_attr(item, "title", "name", "title-long", default="")),
        "nummer": str(
            _attr(item, "course-number", "course-number-short", "number", default="")
        ),
        "semester": str(
            _attr(item, "start-semester", "semester", "start_semester", default="")
        ),
    }


def parse_courses(payload: Any) -> list[dict]:
    return [parse_course(item) for item in _items(payload)]


def filter_courses_by_semester(
    courses: list[dict],
    semester_id: str | None = None,
    semester_name: str | None = None,
) -> list[dict]:
    """Filtert clientseitig, weil die API den Semesterfilter nicht immer anwendet."""
    wanted = {
        value.casefold()
        for value in (semester_id, semester_name)
        if value and value.strip()
    }
    if not wanted:
        return courses
    return [
        course
        for course in courses
        if str(course.get("semester", "")).casefold() in wanted
    ]


def parse_file_ref(item: dict) -> dict:
    return {
        "id": str(item.get("id", "")),
        "name": str(_attr(item, "name", "filename", default="")),
        "groesse": _attr(item, "filesize", "file-size", "size", default=0),
        "parent": _relationship_id(item, "parent"),
    }


def parse_file_refs(payload: Any) -> list[dict]:
    return [parse_file_ref(item) for item in _items(payload)]


def parse_folders(payload: Any) -> list[dict]:
    folders = []
    for item in _items(payload):
        folders.append(
            {
                "id": str(item.get("id", "")),
                "name": str(_attr(item, "name", "title", default="")),
                "parent": _relationship_id(item, "parent"),
            }
        )
    return folders


def parse_events(payload: Any) -> list[dict]:
    events = []
    for item in _items(payload):
        events.append(
            {
                "id": str(item.get("id", "")),
                "titel": str(_attr(item, "title", "name", default="")),
                "start": _attr(item, "start", "start-date", "begin", default=None),
                "ende": _attr(item, "end", "end-date", "finish", default=None),
                "ort": _attr(item, "location", "room", "place", default=""),
            }
        )
    return events


def parse_news(payload: Any) -> list[dict]:
    news = []
    for item in _items(payload):
        news.append(
            {
                "id": str(item.get("id", "")),
                "titel": str(_attr(item, "title", "name", default="")),
                "datum": _attr(
                    item, "date", "mkdate", "chdate", "created", default=None
                ),
            }
        )
    return news


def parse_semesters(payload: Any) -> list[dict]:
    semesters = []
    for item in _items(payload):
        semesters.append(
            {
                "id": str(item.get("id", "")),
                "name": str(_attr(item, "title", "name", default="")),
            }
        )
    return semesters


def parse_user(payload: Any) -> dict:
    items = _items(payload)
    if not items:
        raise LoginFailed("Login-Antwort ohne Nutzerdaten", "studip login erneut ausführen")
    item = items[0]
    return {
        "id": str(item.get("id", "")),
        "username": str(_attr(item, "username", default="")),
        "formatted_name": str(
            _attr(item, "formatted-name", "formatted_name", "name", default="")
        ),
        "email": _attr(item, "email", default=None),
    }


class Client:
    def __init__(
        self,
        base_url: str,
        user: str | None = None,
        password: str | None = None,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = normalize_base_url(base_url)
        self.user = user
        self.password = password
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            follow_redirects=True,
            transport=transport,
            headers={
                "Accept": ACCEPT,
                "User-Agent": f"studip-cli/{__version__}",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _auth(self) -> tuple[str, str] | None:
        if self.user and self.password:
            return (self.user, self.password)
        return None

    def _request(
        self,
        path: str,
        params: dict | None = None,
        *,
        login_check: bool = False,
    ) -> httpx.Response:
        try:
            response = self._client.get(
                path, params=params, auth=self._auth()
            )
        except httpx.TimeoutException as exc:
            raise NetworkError(
                f"Zeitüberschreitung bei {path}",
                "Verbindung prüfen und erneut versuchen",
            ) from exc
        except httpx.HTTPError as exc:
            raise NetworkError(
                f"Netzwerkfehler bei {path}: {exc}",
                "Verbindung prüfen und erneut versuchen",
            ) from exc

        status = response.status_code
        if status in (401, 403):
            if login_check:
                raise LoginFailed(
                    "Login fehlgeschlagen – Benutzer oder Passwort falsch",
                    "Benutzer und Passwort prüfen oder studip login erneut ausführen",
                )
            raise LoginRequired(
                "Login fehlt oder ist abgelaufen",
                "studip login ausführen",
            )
        if status == 404:
            raise NotFound(
                "Nicht gefunden auf der Stud.IP-Instanz",
                "Kurs- oder Dateinamen prüfen",
            )
        if status == 429:
            raise NetworkError(
                "Zu viele Anfragen an Stud.IP",
                "Kurz warten und erneut versuchen",
            )
        if status >= 500:
            raise SourceError(
                f"Stud.IP antwortet mit HTTP {status}",
                "Später erneut versuchen",
            )
        if status >= 400:
            raise SourceError(
                f"Stud.IP lehnt die Anfrage ab (HTTP {status})",
                "Instanz und Berechtigungen prüfen",
            )
        return response

    def _get_json(
        self,
        path: str,
        params: dict | None = None,
        *,
        login_check: bool = False,
    ) -> Any:
        response = self._request(path, params, login_check=login_check)
        try:
            return response.json()
        except ValueError as exc:
            raise SourceError(
                "Stud.IP liefert kein gültiges JSON",
                "Später erneut versuchen oder Instanz prüfen",
            ) from exc

    def users_me(self, login_check: bool = False) -> dict:
        return parse_user(self._get_json(f"{API}/users/me", login_check=login_check))

    def search_courses(
        self,
        query: str | None = None,
        semester: str | None = None,
        semester_name: str | None = None,
    ) -> list[dict]:
        params: dict[str, str] = {}
        if query:
            params["filter[q]"] = query
            params["filter[fields]"] = "title_lecturer_number"
        if semester:
            params["filter[semester]"] = semester
        courses = parse_courses(self._get_json(f"{API}/courses", params))
        return filter_courses_by_semester(courses, semester, semester_name)

    def my_courses(
        self, semester: str | None = None, semester_name: str | None = None
    ) -> list[dict]:
        params: dict[str, str] = {}
        if semester:
            params["filter[semester]"] = semester
        try:
            courses = parse_courses(
                self._get_json(f"{API}/users/me/courses", params)
            )
        except NotFound:
            courses = parse_courses(self._get_json(f"{API}/courses", params))
        return filter_courses_by_semester(courses, semester, semester_name)

    def semesters(self) -> list[dict]:
        return parse_semesters(self._get_json(f"{API}/semesters"))

    def course_folders(self, course_id: str) -> list[dict]:
        return parse_folders(
            self._get_json(f"{API}/courses/{course_id}/folders")
        )

    def course_file_refs(self, course_id: str) -> list[dict]:
        return parse_file_refs(
            self._get_json(f"{API}/courses/{course_id}/file-refs")
        )

    def file_content(self, file_id: str) -> bytes:
        response = self._request(f"{API}/file-refs/{file_id}/content")
        return response.content

    def course_events(self, course_id: str) -> list[dict]:
        return parse_events(
            self._get_json(f"{API}/courses/{course_id}/events")
        )

    def course_news(self, course_id: str) -> list[dict]:
        return parse_news(self._get_json(f"{API}/courses/{course_id}/news"))

    def all_news(self) -> list[dict]:
        return parse_news(self._get_json(f"{API}/studip/news"))
