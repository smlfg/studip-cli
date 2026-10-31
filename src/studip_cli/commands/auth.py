"""`studip login`, `logout` und `whoami`."""

from __future__ import annotations

import getpass
import os

from ..client import Client
from ..config import (
    clear_config,
    config_path,
    credentials_path,
    delete_password,
    env_base_url,
    load_config,
    normalize_base_url,
    resolve_credentials,
    save_config,
    save_password,
)
from ..errors import UsageError
from ..output import emit
from ..ui import is_tty, prompt


def _display_name(user: dict, fallback: str) -> str:
    return (
        user.get("formatted_name")
        or user.get("username")
        or fallback
    )


def run_login(json_mode: bool) -> int:
    stored = load_config()
    env_base = env_base_url()
    env_user = os.environ.get("STUDIP_USER")
    env_password = os.environ.get("STUDIP_PASSWORD")
    stored_base = stored.get("base_url")
    stored_user = stored.get("user")

    if env_user and env_password:
        base_value = env_base or (
            normalize_base_url(stored_base) if stored_base else None
        )
        if not base_value:
            raise UsageError(
                "Stud.IP-Adresse fehlt",
                "STUDIP_BASE_URL setzen oder studip login interaktiv ausführen",
            )
        base_url = base_value
        user = env_user
        password = env_password
    else:
        if not is_tty():
            raise UsageError(
                "STUDIP_USER und STUDIP_PASSWORD fehlen",
                "studip login interaktiv ausführen oder Env-Variablen setzen",
            )
        entered = prompt("Stud.IP-Adresse: ").strip()
        if env_base:
            base_url = env_base
        elif stored_base:
            base_url = normalize_base_url(stored_base)
        else:
            base_url = normalize_base_url(entered)
        user = env_user or stored_user
        if not user:
            user = prompt("Benutzer: ").strip()
        if not user:
            raise UsageError(
                "Benutzer fehlt",
                "studip login erneut ausführen",
            )
        password = env_password
        if not password:
            password = getpass.getpass("Passwort: ")
        if not password:
            raise UsageError(
                "Passwort fehlt",
                "studip login erneut ausführen",
            )

    with Client(base_url, user, password) as client:
        info = client.users_me(login_check=True)

    save_config(base_url, user)
    save_password(base_url, user, password)

    name = _display_name(info, user)
    emit(
        json_mode,
        [f"Login erfolgreich als {name}"],
        {
            "base_url": base_url,
            "user": {
                "id": info.get("id", ""),
                "username": info.get("username") or user,
                "formatted_name": info.get("formatted_name") or name,
            },
        },
    )
    return 0


def run_logout(json_mode: bool) -> int:
    stored = load_config()
    base_url = env_base_url() or stored.get("base_url")
    user = os.environ.get("STUDIP_USER") or stored.get("user")
    existed = (
        config_path().is_file()
        or credentials_path().is_file()
        or bool(stored)
        or bool(os.environ.get("STUDIP_USER"))
    )
    if isinstance(base_url, str) and isinstance(user, str) and base_url and user:
        delete_password(normalize_base_url(base_url), user)
    clear_config()
    text = "Abgemeldet." if existed else "Nicht angemeldet."
    emit(json_mode, [text], {"ok": True})
    return 0


def run_whoami(json_mode: bool) -> int:
    credentials = resolve_credentials()
    assert credentials is not None
    base_url, user, password = credentials
    with Client(base_url, user, password) as client:
        info = client.users_me()

    name = _display_name(info, user)
    username = info.get("username") or user
    lines = [f"Angemeldet als {name} ({username})", f"Instanz: {base_url}"]
    emit(
        json_mode,
        lines,
        {
            "base_url": base_url,
            "user": {
                "id": info.get("id", ""),
                "username": username,
                "formatted_name": info.get("formatted_name") or name,
            },
        },
    )
    return 0
