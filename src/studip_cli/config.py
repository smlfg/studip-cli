"""Konfiguration und Zugangsdaten (Config 0600, Keyring wenn verfügbar)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from .errors import UsageError

SERVICE = "studip-cli"


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base).expanduser() / "studip-cli"
    return Path.home() / ".config" / "studip-cli"


def config_path() -> Path:
    return config_dir() / "config.json"


def credentials_path() -> Path:
    return config_dir() / "credentials.json"


def normalize_base_url(value: str) -> str:
    text = (value or "").strip().rstrip("/")
    if not text:
        raise UsageError(
            "Stud.IP-Adresse fehlt",
            "STUDIP_BASE_URL setzen oder studip login ausführen",
        )
    parts = urlsplit(text)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise UsageError(
            f"Ungültige Stud.IP-Adresse: {value!r}",
            "Adresse mit http:// oder https:// angeben",
        )
    return text


def env_base_url() -> str | None:
    value = os.environ.get("STUDIP_BASE_URL") or os.environ.get("STUDIP_URL")
    if not value:
        return None
    return normalize_base_url(value)


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def load_config() -> dict:
    return _read_json(config_path())


def _write_private(path: Path, data: dict) -> None:
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(directory, 0o700)
    except OSError:
        pass
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def save_config(base_url: str, user: str) -> None:
    _write_private(
        config_path(), {"base_url": base_url.rstrip("/"), "user": user}
    )


def _keyring():
    try:
        import keyring  # type: ignore
    except Exception:  # noqa: BLE001 - optionale Abhängigkeit
        return None
    return keyring


def keyring_key(base_url: str, user: str) -> str:
    return f"{base_url.rstrip('/')}|{user}"


def save_password(base_url: str, user: str, password: str) -> None:
    keyring = _keyring()
    if keyring is not None:
        try:
            keyring.set_password(SERVICE, keyring_key(base_url, user), password)
            return
        except Exception:  # noqa: BLE001 - Rückfall auf Datei
            pass
    _write_private(
        credentials_path(),
        {
            "base_url": base_url.rstrip("/"),
            "user": user,
            "password": password,
        },
    )


def load_password(base_url: str, user: str) -> str | None:
    keyring = _keyring()
    if keyring is not None:
        try:
            value = keyring.get_password(SERVICE, keyring_key(base_url, user))
        except Exception:  # noqa: BLE001 - Rückfall auf Datei
            value = None
        if value:
            return value
    data = _read_json(credentials_path())
    password = data.get("password")
    if isinstance(password, str) and password:
        return password
    return None


def delete_password(base_url: str, user: str) -> None:
    keyring = _keyring()
    if keyring is not None:
        try:
            keyring.delete_password(SERVICE, keyring_key(base_url, user))
        except Exception:  # noqa: BLE001 - Eintrag kann fehlen
            pass
    try:
        credentials_path().unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass


def clear_config() -> None:
    for path in (config_path(), credentials_path()):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass


def resolve_base_url(required: bool = True) -> str | None:
    value = env_base_url()
    if value:
        return value
    stored = load_config().get("base_url")
    if isinstance(stored, str) and stored.strip():
        return normalize_base_url(stored)
    if required:
        from .errors import LoginRequired

        raise LoginRequired(
            "Stud.IP-Adresse fehlt",
            "studip login ausführen oder STUDIP_BASE_URL setzen",
        )
    return None


def resolve_user() -> str | None:
    value = os.environ.get("STUDIP_USER")
    if value:
        return value
    stored = load_config().get("user")
    return stored if isinstance(stored, str) and stored else None


def resolve_credentials(required: bool = True) -> tuple[str, str, str] | None:
    from .errors import LoginRequired

    base_url = resolve_base_url(required=required)
    if base_url is None:
        return None
    user = resolve_user()
    password = os.environ.get("STUDIP_PASSWORD")
    if not password and user:
        password = load_password(base_url, user)
    if not user or not password:
        if required:
            raise LoginRequired()
        return None
    return base_url, user, password
