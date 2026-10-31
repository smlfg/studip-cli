"""Kommandozeile für studip."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from . import __version__
from .commands import dateien, download, kurse, termine
from .errors import StudipError, UsageError
from .output import emit_json


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message)


def _version() -> str:
    return f"%(prog)s {__version__}"


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="studip",
        description=(
            "Stud.IP im Terminal: Kurse, Dateien, Termine und Ankündigungen "
            "über die offizielle JSON:API."
        ),
    )
    parser.add_argument("--version", action="version", version=_version())
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON ausgeben (auch wenn stdout kein Terminal ist)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    kurse_parser = subparsers.add_parser(
        "kurse", help="Kurse suchen oder eigene Kurse auflisten"
    )
    kurse_parser.add_argument(
        "suchbegriff", nargs="?", help="Suchbegriff (Name oder Teil des Namens)"
    )
    kurse_parser.add_argument(
        "--semester", help="Semestername oder Semester-ID"
    )
    kurse_parser.set_defaults(handler=_run_kurse)

    dateien_parser = subparsers.add_parser(
        "dateien", help="Ordner und Dateien eines Kurses anzeigen"
    )
    dateien_parser.add_argument("kursname", help="Kursname (oder Teil davon)")
    dateien_parser.set_defaults(handler=_run_dateien)

    download_parser = subparsers.add_parser(
        "download", help="Datei(en) eines Kurses lokal speichern"
    )
    download_parser.add_argument("kursname", help="Kursname (oder Teil davon)")
    download_parser.add_argument(
        "dateiname", nargs="?", help="Dateiname; ohne Angabe alle Dateien"
    )
    download_parser.add_argument("--ziel", help="Zielordner (Standard: ~/Downloads)")
    download_parser.add_argument(
        "--ja", action="store_true", help="Vorhandene Dateien ohne Nachfrage überschreiben"
    )
    download_parser.set_defaults(handler=_run_download)

    termine_parser = subparsers.add_parser(
        "termine", help="Termine eines Kurses oder der eigenen Kurse anzeigen"
    )
    termine_parser.add_argument(
        "kursname", nargs="?", help="Kursname; ohne Angabe alle eigenen Kurse"
    )
    termine_parser.set_defaults(handler=_run_termine)

    return parser


def _run_kurse(args: argparse.Namespace, json_mode: bool) -> int:
    return kurse.run(json_mode, args.suchbegriff, args.semester)


def _run_dateien(args: argparse.Namespace, json_mode: bool) -> int:
    return dateien.run(json_mode, args.kursname)


def _run_download(args: argparse.Namespace, json_mode: bool) -> int:
    return download.run(
        json_mode, args.kursname, args.dateiname, args.ziel, args.ja
    )


def _run_termine(args: argparse.Namespace, json_mode: bool) -> int:
    return termine.run(json_mode, args.kursname)


def _split_json(argv: list[str]) -> tuple[bool, list[str]]:
    forced = False
    cleaned: list[str] = []
    for token in argv:
        if token == "--json":
            forced = True
        else:
            cleaned.append(token)
    return forced, cleaned


def _validate_heute() -> None:
    value = os.environ.get("STUDIP_HEUTE")
    if not value:
        return
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise UsageError(
            f"Ungültiges STUDIP_HEUTE: {value!r}",
            "STUDIP_HEUTE als JJJJ-MM-TT setzen",
        ) from exc


def _emit_error(json_mode: bool, error: StudipError) -> None:
    if json_mode:
        emit_json(error.as_json())
        return
    sys.stderr.write(f"Fehler: {error.message}\n")
    if error.next_step:
        sys.stderr.write(f"Nächster Schritt: {error.next_step}\n")
    sys.stderr.flush()


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    forced_json, cleaned = _split_json(raw)
    json_mode = forced_json or not sys.stdout.isatty()
    try:
        parser = build_parser()
        args = parser.parse_args(cleaned)
        _validate_heute()
        return int(args.handler(args, json_mode) or 0)
    except StudipError as error:
        _emit_error(json_mode, error)
        return error.exit_code
    except KeyboardInterrupt:
        _emit_error(
            json_mode,
            StudipError("aborted", "Abgebrochen.", "Erneut ausführen", 130),
        )
        return 130
    except EOFError:
        _emit_error(
            json_mode,
            UsageError("Eingabe abgebrochen", "studip login erneut ausführen"),
        )
        return 2
    except BrokenPipeError:
        return 1
    except Exception as exc:  # noqa: BLE001 - niemals Traceback im Terminal
        _emit_error(
            json_mode,
            StudipError(
                "internal",
                f"Unerwarteter Fehler: {exc}",
                "studip --help anzeigen oder Support informieren",
                1,
            ),
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
