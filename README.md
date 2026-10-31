# studip-cli

Stud.IP im Terminal: Kurse, Dateien, Termine und Ankündigungen über die
offizielle JSON:API (`/jsonapi.php/v1/`). Funktioniert mit jeder Stud.IP-Instanz,
die die JSON:API aktiviert hat.

## Schnellstart

```bash
pipx install git+https://github.com/smlfg/studip-cli
studip login
studip kurse physik
studip dateien "Physik I: Mechanik"
studip download "Physik I: Mechanik" "Skript.pdf"
```

`studip login` fragt nach Instanz, Benutzer und Passwort. Das Passwort wird
verdeckt eingegeben und im Schlüsselbund (sonst in einer Datei mit Rechten
0600 unter `~/.config/studip-cli/`) gespeichert. `STUDIP_BASE_URL`
überschreibt die Instanz-URL, `STUDIP_USER` und `STUDIP_PASSWORD` überschreiben
die gespeicherten Zugangsdaten (für Agenten und den Fake-Server im Test).

## Befehle

- `studip login` – interaktiv anmelden
- `studip logout` – gespeicherte Sitzung löschen (idempotent)
- `studip whoami` – angemeldeten Nutzer anzeigen
- `studip kurse [SUCHBEGRIFF] [--semester]` – Kurse suchen/auflisten
- `studip dateien KURSNAME` – Ordner und Dateien eines Kurses
- `studip download KURSNAME [DATEINAME] [--ziel ORDNER]` – Datei lokal speichern
- `studip termine [KURSNAME]` – Termine anzeigen
- `studip news [KURSNAME]` – Ankündigungen anzeigen

Beispiele:

```bash
studip login
studip whoami
studip kurse physik
studip kurse --semester "WiSe 2026/27"
studip dateien "Physik I: Mechanik"
studip download "Physik I: Mechanik" "Skript.pdf"
studip download "Physik I: Mechanik" --ziel ~/Stud.IP
studip termine "Physik I: Mechanik"
studip news "Physik I: Mechanik"
studip kurse physik --json
```

Kursnamen und Suchbegriffe werden positional übergeben. Genau ein Treffer wird
direkt verwendet; bei mehreren Treffern bietet das Tool im TTY eine
nummerierte Auswahl. Ohne TTY erscheint die Liste mit Exit-Code 2, damit ein
Agent einen eindeutigeren Namen wählen kann. Lesende Befehle geben im Terminal
lesbaren Text aus, mit `--json` oder wenn stdout kein TTY ist JSON.

## Konfiguration

Die Instanz wird über `STUDIP_BASE_URL` (oder `STUDIP_URL`) gesetzt und
überschreibt die gespeicherte Adresse. `STUDIP_USER` und `STUDIP_PASSWORD`
überschreiben die Config; `STUDIP_HEUTE=JJJJ-MM-TT` macht Termin-Ausgaben für
Tests deterministisch.

Gespeichert wird unter `${XDG_CONFIG_HOME:-~/.config}/studip-cli/`:

- `config.json` (0600) mit Instanz-URL und Benutzername
- Passwort im Schlüsselbund (Dienst `studip-cli`), sonst `credentials.json`
  (0600)

Passwörter erscheinen nie in Ausgaben, Logs oder Kommandozeilen-Flags.
`studip logout` entfernt alles wieder. Standard-Ziel für Downloads ist
`~/Downloads`; `--ziel` überschreibt es. Vorhandene Dateien werden ohne
Nachfrage nicht überschrieben, `--ja` erlaubt es ohne Rückfrage.

## Ausgabe und Exit-Codes

Standard ist lesbarer Text im Terminal. JSON gibt es mit `--json` oder wenn
stdout kein TTY ist; Prompts und Fehler gehen auf stderr, ohne Traceback.

| Code | Bedeutung |
|---:|---|
| 0 | Erfolg (auch „keine Treffer“) |
| 1 | Allgemeiner Fehler, z. B. kein Kurs, Überschreiben abgelehnt, lokaler Schreibfehler |
| 2 | Usage: falsche Argumente, mehrdeutiger Name ohne TTY, ungültige Env |
| 3 | Netz oder Quelle: Timeout, DNS/TLS, HTTP 5xx/429, ungültige Antwort |
| 4 | Login nötig oder fehlgeschlagen (401/403, fehlende Zugangsdaten) |
| 130 | Abbruch mit Strg+C |

Fehlermeldungen nennen den nächsten Schritt, z. B.
`Login fehlt – studip login ausführen`.

## Inoffiziell

`studip-cli` ist kein Angebot der Stud.IP-Entwickler oder einer Hochschule. Es
nutzt die dokumentierte JSON:API, kann sich mit Stud.IP-Versionen ändern und
wurde live nur lesend gegen öffentliche Seiten und Endpunkte geprüft. Es gibt
keine schreibende Web-Aktion: Anlegen, Bearbeiten, Hochladen und Löschen sind
nicht Teil des Tools. Der einzige Schreibvorgang ist der lokale Download.
Fixtures und Beispiele sind anonymisiert; Mails enden auf `example.invalid`.

## Entwicklung

Die verbindliche UX-Spec steht in [`docs/UX.md`](docs/UX.md), der Vertrag in
[`INTERFACE.md`](INTERFACE.md), die Anforderungen in
[`ANFORDERUNGEN.md`](ANFORDERUNGEN.md). Vor dem Bau:

```bash
python3 tests/harness/ux_check.py . --spec-only
pytest -q tests/acceptance
pytest -q tests/harness
```

## Lizenz

MIT – Copyright (c) 2026 smlfg. Siehe [`LICENSE`](LICENSE).
