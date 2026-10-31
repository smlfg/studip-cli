# UX-Gate-Bericht

- Datum: 2026-10-31
- Tool: `studip`
- Repo: `smlfg/studip-cli`

## ux_check.py

- Befehl: `python3 tests/harness/ux_check.py . --report scratch/ux_check.md`
- Exit-Code: `0`
- Ergebnis: PASS

| ID | Ergebnis | Befund |
|---|---|---|
| UX00 | PASS | 8 Request(s) am Fake-Server, keine Fremdverbindung |
| UX01 | PASS | docs/UX.md: 4 Sitzungen, 0 formsteps |
| UX02 | PASS | Credential-Env STUDIP_PASSWORD, STUDIP_USER über `login` |
| UX03 | PASS | --help, --version und 8 Unterkommandos mit Exit 0 |
| UX04 | PASS | 8 Unterkommandos ohne Pflicht-Option statt positional |
| UX05 | PASS | 4 Sitzungen ohne JSON/Traceback im TTY |
| UX06 | PASS | Schnellstart: 4 Tool-Befehle, Installation passt |
| UX07 | PASS | keine ux-formsteps, keine schreibende Aktion |
| UX08 | PASS | keine ux-formsteps, keine schreibende Aktion |
| UX09 | SKIP | keine schreibende Sitzung |

## ux_session.py

- Befehl: `python3 tests/harness/ux_session.py . --report scratch/ux_session.md`
- Exit-Code: `0`
- Ergebnis: PASS

| Sitzung | Lauf | Ergebnis | Befund |
|---|---|---|---|
| Installation und erster Login | 1 | PASS | OK |
| Kurse nach Namen suchen | 1 | PASS | OK |
| Dateien eines Kurses anzeigen | 1 | PASS | OK |
| Eine Datei herunterladen | 1 | PASS | OK |

## Tests

- Befehl: `scratch/venv/bin/pytest -q`
- Ergebnis: `38 passed`
