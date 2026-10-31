from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRATCH = REPO / "scratch" / "tmp"


def _workspace() -> Path:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="studip-contract-", dir=SCRATCH))


def _run(args: list[str], env_overrides: dict[str, str] | None = None):
    workspace = _workspace()
    env = os.environ.copy()
    for name in ("STUDIP_BASE_URL", "STUDIP_URL", "STUDIP_USER", "STUDIP_PASSWORD", "STUDIP_HEUTE"):
        env.pop(name, None)
    env.update(
        {
            "HOME": str(workspace / "home"),
            "XDG_CONFIG_HOME": str(workspace / "config"),
            "PYTHONPATH": str(REPO / "src"),
            "PYTHONIOENCODING": "utf-8",
            "NO_COLOR": "1",
        }
    )
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "studip_cli", *args],
        cwd=str(REPO),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
    )


def test_version_und_help_mit_exit_0():
    for args in (["--version"], ["--help"]):
        result = _run(args)
        assert result.returncode == 0, result.stderr
        assert "Traceback" not in result.stdout + result.stderr
    for sub in (
        "login",
        "logout",
        "whoami",
        "kurse",
        "dateien",
        "download",
        "termine",
        "news",
    ):
        result = _run([sub, "--help"])
        assert result.returncode == 0, (sub, result.stderr)


def test_unbekanntes_unterkommando_mit_json_ist_ein_objekt():
    result = _run(["--json", "gibt-es-nicht"])
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "usage"


def test_ungueltiges_studip_heute_ist_usage():
    result = _run(["kurse", "physik"], {"STUDIP_HEUTE": "31.10.2026"})
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "usage"
    assert "STUDIP_HEUTE" in payload["error"]["message"]
    assert "Traceback" not in result.stderr


def test_login_ohne_tty_und_ohne_zugangsdaten_ist_usage():
    result = _run(["login"])
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "usage"
    assert "studip login" in payload["error"]["next"]
    assert "Traceback" not in result.stderr


def test_whoami_ohne_login_nennt_naechsten_schritt():
    result = _run(["whoami"])
    assert result.returncode == 4
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "login_required"
    assert "studip login" in payload["error"]["next"]
    assert "Traceback" not in result.stderr
