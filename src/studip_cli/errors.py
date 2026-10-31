"""Fehlerklassen mit stabilen Codes, Exit-Codes und nächstem Schritt."""

from __future__ import annotations


class StudipError(Exception):
    """Ein erwarteter Fehler, der lesbar ausgegeben wird (kein Traceback)."""

    def __init__(
        self,
        code: str,
        message: str,
        next_step: str = "",
        exit_code: int = 1,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.next_step = next_step
        self.exit_code = exit_code

    def as_json(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "next": self.next_step,
            }
        }


class UsageError(StudipError):
    def __init__(self, message: str, next_step: str = "studip --help") -> None:
        super().__init__("usage", message, next_step, 2)


class NetworkError(StudipError):
    def __init__(self, message: str, next_step: str = "Verbindung prüfen und erneut versuchen") -> None:
        super().__init__("network", message, next_step, 3)


class SourceError(StudipError):
    def __init__(self, message: str, next_step: str = "Später erneut versuchen oder Instanz prüfen") -> None:
        super().__init__("source", message, next_step, 3)


class LoginRequired(StudipError):
    def __init__(
        self,
        message: str = "Login fehlt",
        next_step: str = "studip login ausführen",
    ) -> None:
        super().__init__("login_required", message, next_step, 4)


class LoginFailed(StudipError):
    def __init__(
        self,
        message: str = "Login fehlgeschlagen",
        next_step: str = "Benutzer und Passwort prüfen oder studip login erneut ausführen",
    ) -> None:
        super().__init__("login_failed", message, next_step, 4)


class NotFound(StudipError):
    def __init__(self, message: str, next_step: str = "") -> None:
        super().__init__("not_found", message, next_step, 1)


class FileExists(StudipError):
    def __init__(self, message: str, next_step: str = "Anderen Dateinamen wählen oder --ja verwenden") -> None:
        super().__init__("file_exists", message, next_step, 1)


class Aborted(StudipError):
    def __init__(self, message: str, next_step: str = "") -> None:
        super().__init__("aborted", message, next_step, 1)
