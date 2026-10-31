"""`studip dateien`: Ordner und Dateien eines Kurses anzeigen."""

from __future__ import annotations

from ..format import format_course, format_size
from ..output import emit
from ..resolve import resolve_course
from .common import session_client


def run(json_mode: bool, kursname: str) -> int:
    with session_client() as client:
        course = resolve_course(client, kursname)
        folders = client.course_folders(course["id"])
        files = client.course_file_refs(course["id"])

    by_folder: dict[str, list[dict]] = {}
    known = {folder["id"] for folder in folders}
    orphans: list[dict] = []
    for item in files:
        parent = item.get("parent")
        if parent and parent in known:
            by_folder.setdefault(parent, []).append(item)
        else:
            orphans.append(item)

    groups = []
    for folder in folders:
        groups.append(
            {
                "name": folder["name"],
                "dateien": [
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "groesse": item["groesse"],
                    }
                    for item in by_folder.get(folder["id"], [])
                ],
            }
        )
    if orphans:
        groups.append(
            {
                "name": "",
                "dateien": [
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "groesse": item["groesse"],
                    }
                    for item in orphans
                ],
            }
        )

    lines = [f"Kurs: {format_course(course['titel'], course['nummer'])}"]
    if not any(group["dateien"] for group in groups):
        lines.append("Keine Dateien gefunden.")
    else:
        for group in groups:
            if not group["dateien"]:
                continue
            if group["name"]:
                lines.append(f"[Ordner] {group['name']}")
                prefix = "  "
            else:
                prefix = ""
            for item in group["dateien"]:
                lines.append(
                    f"{prefix}{item['name']} ({format_size(item['groesse'])})"
                )

    payload = {
        "kurs": {
            "id": course["id"],
            "titel": course["titel"],
            "nummer": course["nummer"],
        },
        "ordner": groups,
    }
    emit(json_mode, lines, payload)
    return 0
