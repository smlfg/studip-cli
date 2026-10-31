from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from studip_cli.client import Client, parse_courses, parse_file_refs
from studip_cli.commands.common import resolve_semester
from studip_cli.errors import LoginFailed, LoginRequired, NetworkError, SourceError
from studip_cli.format import format_size

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "ux"


def _payload(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_parse_courses_aus_fixture():
    courses = parse_courses(_payload("kurse_physik.json"))
    assert [course["titel"] for course in courses] == [
        "Physik I: Mechanik",
        "Physik II: Elektrodynamik",
    ]
    assert courses[0]["nummer"] == "PHY-101"
    assert courses[0]["semester"] == "WiSe 2026/27"


def test_parse_file_refs_aus_fixture():
    files = parse_file_refs(_payload("dateien_phy1.json"))
    assert [item["name"] for item in files] == [
        "Skript.pdf",
        "Übungsblatt-01.pdf",
        "Lösung-01.pdf",
    ]
    assert files[0]["parent"] == "folder-material"
    assert files[0]["groesse"] == 12288


def test_groesse_deutsch():
    assert format_size(12288) == "12,0 kB"
    assert format_size(353280) == "345,0 kB"
    assert format_size(12) == "12 B"


def _client(handler, **kwargs) -> Client:
    return Client(
        "https://demo.studip.de",
        user="max.mustermann@example.invalid",
        password="geheim",
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


def test_kurssuche_setzt_filter_und_basic_auth():
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = parse_qs(urlsplit(str(request.url)).query)
        seen["auth"] = request.headers.get("Authorization")
        seen["accept"] = request.headers.get("Accept")
        return httpx.Response(
            200,
            json=_payload("kurse_physik.json"),
            headers={"Content-Type": "application/vnd.api+json"},
        )

    with _client(handler) as client:
        courses = client.search_courses("physik")

    assert len(courses) == 2
    assert seen["path"] == "/jsonapi.php/v1/courses"
    assert seen["query"]["filter[q]"] == ["physik"]
    assert seen["auth"].startswith("Basic ")
    assert seen["accept"] == "application/vnd.api+json"


def test_kurssuche_filtert_semester_clientseitig():
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["query"] = parse_qs(urlsplit(str(request.url)).query)
        return httpx.Response(
            200,
            json=_payload("kurse_gemischt.json"),
            headers={"Content-Type": "application/vnd.api+json"},
        )

    with _client(handler) as client:
        courses = client.search_courses(
            "physik", "wise-2026", "WiSe 2026/27"
        )

    assert [course["id"] for course in courses] == ["phy-1", "phy-3"]
    assert seen["query"]["filter[q]"] == ["physik"]
    assert seen["query"]["filter[semester]"] == ["wise-2026"]


def test_eigene_kurse_filtert_semester_clientseitig():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_payload("kurse_gemischt.json"),
            headers={"Content-Type": "application/vnd.api+json"},
        )

    with _client(handler) as client:
        courses = client.my_courses("wise-2026", "WiSe 2026/27")

    assert [course["id"] for course in courses] == ["phy-1", "phy-3"]


def test_resolve_semester_liefert_id_und_name():
    payload = {
        "data": [
            {"type": "semesters", "id": "wise-2026", "attributes": {"title": "WiSe 2026/27"}}
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=payload,
            headers={"Content-Type": "application/vnd.api+json"},
        )

    expected = ("wise-2026", "WiSe 2026/27")
    with _client(handler) as client:
        assert resolve_semester(client, "WiSe 2026/27") == expected
        assert resolve_semester(client, "wise-2026") == expected


def test_http_401_wird_login_required():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    with _client(handler) as client:
        with pytest.raises(LoginRequired):
            client.search_courses("physik")


def test_login_pruefung_unterscheidet_falsches_passwort():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403)

    with _client(handler) as client:
        with pytest.raises(LoginFailed):
            client.users_me(login_check=True)


def test_kaputtes_json_ist_quellenfehler():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>kein json</html>")

    with _client(handler) as client:
        with pytest.raises(SourceError):
            client.search_courses("physik")


def test_netzwerkfehler_ist_network_exit_3():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("kein netz", request=request)

    with _client(handler) as client:
        with pytest.raises(NetworkError) as info:
            client.search_courses("physik")
    assert info.value.exit_code == 3
