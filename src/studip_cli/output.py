"""Ausgabe: lesbarer Text im TTY, sonst genau ein JSON-Objekt."""

from __future__ import annotations

import json
from typing import Iterable


def emit_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def emit(json_mode: bool, lines: Iterable[str], payload: object) -> None:
    if json_mode:
        emit_json(payload)
        return
    for line in lines:
        print(line)
