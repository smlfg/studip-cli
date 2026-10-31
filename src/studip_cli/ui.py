"""Terminal-Eingaben und Auswahl (Prompts gehen auf stderr)."""

from __future__ import annotations

import sys
from typing import Callable, Sequence, TypeVar

from .errors import UsageError

T = TypeVar("T")


def is_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def prompt(text: str) -> str:
    sys.stderr.write(text)
    sys.stderr.flush()
    line = sys.stdin.readline()
    if line == "":
        raise UsageError(
            "Eingabe abgebrochen",
            "studip login erneut ausführen oder Env-Variablen setzen",
        )
    return line.rstrip("\r\n")


def choose(items: Sequence[T], label: Callable[[T], str], what: str) -> T:
    if not items:
        raise UsageError(f"Keine {what} zur Auswahl")
    if len(items) == 1:
        return items[0]
    if not is_tty():
        raise UsageError(
            f"Mehrere {what} gefunden",
            "Eindeutigeren Namen angeben",
        )
    for index, item in enumerate(items, start=1):
        sys.stderr.write(f"{index}) {label(item)}\n")
    while True:
        answer = prompt(f"Auswahl [1-{len(items)}]: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(items):
            return items[int(answer) - 1]
        sys.stderr.write(f"Bitte eine Zahl von 1 bis {len(items)} eingeben.\n")
