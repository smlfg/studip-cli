"""Akzeptanztests für die Sitzungen aus docs/UX.md.

Jeder Test startet das Tool als Subprozess in einem Pseudo-Terminal gegen den
Fake-Server aus tests/harness/fake_server.py und prüft die Kernausgaben der
UX-Sitzung. Der Tool-Code entsteht erst in Schritt 4; bis dahin dürfen diese
Tests rot sein.
"""

from __future__ import annotations

import os
import pty
import re
import select
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
UX_FILE = REPO / "docs" / "UX.md"
FIXTURES = REPO / "tests" / "fixtures" / "ux"
HARNESS = REPO / "tests" / "harness"

sys.path.insert(0, str(HARNESS))

from fake_server import FakeServer  # noqa: E402
from ux_spec import parse as parse_ux  # noqa: E402

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def _studip_command() -> list[str]:
    override = os.environ.get("STUDIP_BIN", "").strip()
    if override:
        return shlex.split(override)
    installed = shutil.which("studip")
    if installed:
        return [installed]
    return [sys.executable, "-m", "studip_cli"]


def _workspace() -> tempfile.TemporaryDirectory[str]:
    base = REPO / "scratch" / "tmp"
    base.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="studip-acceptance-", dir=base)


def _environment(workspace: Path, base_url: str) -> tuple[dict[str, str], Path]:
    home = workspace / "home"
    home.mkdir(parents=True, exist_ok=True)
    config = workspace / "config"
    cache = workspace / "cache"
    pythonpath = [str(REPO / "src"), str(REPO)]
    if os.environ.get("PYTHONPATH"):
        pythonpath.append(os.environ["PYTHONPATH"])
    env = os.environ.copy()
    env.update(
        {
            "STUDIP_BASE_URL": base_url,
            "STUDIP_USER": "max.mustermann@example.invalid",
            "STUDIP_PASSWORD": "geheim",
            "STUDIP_HEUTE": "2026-10-31",
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(config),
            "XDG_CACHE_HOME": str(cache),
            "XDG_DOWNLOAD_DIR": str(home / "Downloads"),
            "PYTHONPATH": os.pathsep.join(pythonpath),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUNBUFFERED": "1",
            "NO_COLOR": "1",
            "TERM": "xterm-256color",
        }
    )
    return env, home


def _run_in_pty(
    args: list[str], env: dict[str, str], cwd: Path, timeout: float = 30.0
) -> tuple[int, str]:
    master, slave = pty.openpty()
    proc = subprocess.Popen(
        _studip_command() + args,
        stdin=slave,
        stdout=slave,
        stderr=slave,
        cwd=str(cwd),
        env=env,
        close_fds=True,
        start_new_session=True,
    )
    os.close(slave)
    chunks: list[bytes] = []
    deadline = time.monotonic() + timeout
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                proc.kill()
                break
            readable, _, _ = select.select([master], [], [], min(remaining, 0.2))
            if readable:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
            elif proc.poll() is not None:
                break
        proc.wait(timeout=5)
    finally:
        os.close(master)
    output = b"".join(chunks).decode("utf-8", "replace")
    return proc.returncode, ANSI_RE.sub("", output)


@pytest.fixture(scope="module")
def ux_spec():
    spec = parse_ux(UX_FILE)
    assert not spec.errors, spec.errors
    return spec


@pytest.fixture()
def ux_server(ux_spec):
    with FakeServer(ux_spec, REPO) as server:
        yield server


@pytest.fixture()
def workspace():
    with _workspace() as directory:
        yield Path(directory)


def _request_paths(server: FakeServer) -> list[str]:
    return [request.path for request in server.requests]


def test_login_session_speichert_und_meldet_erfolg(ux_server, workspace):
    env, _home = _environment(workspace, ux_server.base_url)

    code, output = _run_in_pty(["login"], env, REPO)

    assert code == 0, output
    assert "Login erfolgreich als Max Mustermann" in output
    assert "/jsonapi.php/v1/users/me" in _request_paths(ux_server)


def test_kurse_session_zeigt_titel_und_nummer(ux_server, workspace):
    env, _home = _environment(workspace, ux_server.base_url)

    code, output = _run_in_pty(["kurse", "physik"], env, REPO)

    assert code == 0, output
    assert "Physik I: Mechanik (PHY-101)" in output
    assert "Physik II: Elektrodynamik (PHY-201)" in output
    courses = [
        request
        for request in ux_server.requests
        if request.path == "/jsonapi.php/v1/courses"
    ]
    assert courses, "Kurssuche hat /jsonapi.php/v1/courses nicht angefragt"
    assert any("filter%5Bq%5D" in request.query for request in courses)


def test_dateien_session_zeigt_ordner_und_dateien(ux_server, workspace):
    env, _home = _environment(workspace, ux_server.base_url)

    code, output = _run_in_pty(["dateien", "Physik I: Mechanik"], env, REPO)

    assert code == 0, output
    for expected in (
        "Kurs: Physik I: Mechanik (PHY-101)",
        "Materialien",
        "Skript.pdf",
        "Übungsblatt-01.pdf",
        "Übungen",
        "Lösung-01.pdf",
    ):
        assert expected in output
    paths = _request_paths(ux_server)
    assert "/jsonapi.php/v1/courses/phy-1/folders" in paths
    assert "/jsonapi.php/v1/courses/phy-1/file-refs" in paths


def test_download_session_speichert_datei_inhalt(ux_server, workspace):
    env, home = _environment(workspace, ux_server.base_url)

    code, output = _run_in_pty(
        ["download", "Physik I: Mechanik", "Skript.pdf"], env, REPO
    )

    assert code == 0, output
    assert "Skript.pdf" in output
    assert "Gespeichert" in output
    target = home / "Downloads" / "Skript.pdf"
    assert target.is_file(), output
    assert target.read_bytes() == (FIXTURES / "skript.pdf").read_bytes()
    assert "/jsonapi.php/v1/file-refs/fref-skript/content" in _request_paths(
        ux_server
    )
