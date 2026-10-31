"""`studip download`: Dateien eines Kurses lokal speichern."""

from __future__ import annotations

import os
from pathlib import Path

from ..errors import Aborted, FileExists, StudipError
from ..format import format_course, format_size
from ..output import emit
from ..resolve import resolve_course, resolve_course_files
from ..ui import is_tty, prompt
from .common import session_client


def _target_dir(ziel: str | None) -> Path:
    if ziel:
        return Path(ziel).expanduser()
    configured = os.environ.get("XDG_DOWNLOAD_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / "Downloads"


def _ask_overwrite(path: Path) -> bool:
    answer = prompt(
        f"Datei existiert bereits: {path} Überschreiben? [j/N] "
    ).strip().casefold()
    return answer in {"j", "ja", "y", "yes"}


def run(
    json_mode: bool,
    kursname: str,
    dateiname: str | None = None,
    ziel: str | None = None,
    ja: bool = False,
) -> int:
    with session_client() as client:
        course = resolve_course(client, kursname)
        files = client.course_file_refs(course["id"])
        if dateiname:
            selected = resolve_course_files(files, dateiname)
        else:
            selected = files

        if not selected:
            emit(
                json_mode,
                [f"Kurs: {format_course(course['titel'], course['nummer'])}", "Keine Dateien gefunden."],
                {
                    "kurs": {
                        "id": course["id"],
                        "titel": course["titel"],
                        "nummer": course["nummer"],
                    },
                    "dateien": [],
                },
            )
            return 0

        directory = _target_dir(ziel)
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StudipError(
                "internal",
                f"Zielordner konnte nicht angelegt werden: {directory} ({exc})",
                "Schreibrechte prüfen oder --ziel angeben",
                1,
            ) from exc

        saved: list[dict] = []
        lines = [f"Kurs: {format_course(course['titel'], course['nummer'])}"]
        for item in selected:
            name = Path(item["name"]).name or item["id"]
            path = directory / name
            if path.exists() and not ja:
                if not is_tty():
                    raise FileExists(
                        f"Datei existiert bereits: {path}",
                        "Anderen Dateinamen wählen oder --ja verwenden",
                    )
                if not _ask_overwrite(path):
                    raise Aborted(
                        "Abgebrochen, Datei nicht überschrieben.",
                        "Anderen Dateinamen wählen oder --ja verwenden",
                    )
            content = client.file_content(item["id"])
            try:
                path.write_bytes(content)
            except OSError as exc:
                raise StudipError(
                    "internal",
                    f"Datei konnte nicht gespeichert werden: {path} ({exc})",
                    "Schreibrechte prüfen oder --ziel angeben",
                    1,
                ) from exc
            size = item.get("groesse")
            try:
                size = int(size)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                size = 0
            if size <= 0:
                size = len(content)
            saved.append(
                {
                    "name": name,
                    "pfad": str(path),
                    "groesse": size,
                }
            )
            lines.append(f"Datei: {name} ({format_size(size)})")
            lines.append(f"Gespeichert: {name}")

    if json_mode:
        emit(
            True,
            [],
            {
                "kurs": {
                    "id": course["id"],
                    "titel": course["titel"],
                    "nummer": course["nummer"],
                },
                "dateien": saved,
            },
        )
    else:
        emit(False, lines, {})
    return 0
