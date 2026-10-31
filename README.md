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
verdeckt eingegeben und im Schlüsselbund (sonst in einer Config-Datei mit
Rechten 0600 unter `~/.config/studip-cli/`) gespeichert. `STUDIP_BASE_URL`
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

Kursnamen und Suchbegriffe werden positional übergeben. Bei mehreren Treffern
bietet das Tool im TTY eine nummerierte Auswahl; ohne TTY erscheint die Liste
mit Exit-Code 2. Lesende Befehle geben im Terminal lesbaren Text aus, mit
`--json` oder wenn stdout kein TTY ist JSON.

## Schritt 0: UX-Spec zuerst

Der komplette Ablauf steht in
[agent-learnings/WORKFLOW.md](https://github.com/smlfg/agent-learnings/blob/main/WORKFLOW.md).

1. Vor jeder Codezeile `docs/UX.md` ausfüllen: die wichtigsten
   Nutzer-Aufgaben als abtippbare Terminal-Sitzungen, dazu alle Routen und
   Fixtures unter `tests/fixtures/ux/`.
2. Spec prüfen: `python3 tests/harness/ux_spec.py docs/UX.md`
3. Gate nach dem Bau (beide müssen grün sein, sonst ist der Build nicht fertig):
   - `python3 tests/harness/ux_check.py .`
   - `python3 tests/harness/ux_session.py .`

`tests/harness/` wird unverändert aus agent-learnings übernommen.

## Pflichtregel: Bedienbarkeit für Menschen

Jede CLI muss für Menschen bedienbar sein: `login`-Kommando statt nur Env,
Namen statt IDs, interaktive Bestätigung im TTY, `--confirm`/`--ja` nur für
Agenten, README-Schnellstart.

- `login` fragt im Terminal interaktiv (Passwort per getpass) und speichert
  im Schlüsselbund oder in einer Config-Datei mit 0600; dazu `logout` und
  `whoami`/`status` ohne Passwort-Ausgabe. Env-Variablen überschreiben die
  Config (für Agenten).
- Namen/Freitext positional (`studip kurse physik`); mehrere Treffer →
  nummerierte Auswahl im TTY, ohne TTY Liste + Exit Usage.
- Schreibende Aktionen: im TTY „… verbindlich? [j/N]“; `--confirm`/`--yes`
  nur für Agenten; ohne TTY und ohne Flag kein Request. `studip-cli` hat
  keine schreibende Web-Aktion; der Download fragt nur vor dem Überschreiben.
- Terminal-Ausgabe lesbar; JSON mit `--json` oder wenn stdout kein Terminal ist.
- Fehler nennen den nächsten Schritt, keine Tracebacks bei EOF/Strg+C/fehlender
  optionaler Abhängigkeit.
- README beginnt mit „Schnellstart“: `pipx install git+https://github.com/smlfg/<repo>`,
  Login, ein typischer Befehl.

## Sicherheit

Keine Secrets, keine echten Personendaten in Repo, Fixtures oder Logs. Fixtures
sind anonymisiert; Mails enden auf `example.invalid`. Live-Tests sind lesend.
