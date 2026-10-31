# Interface: studip-cli

Kommando im PATH: `studip`. Python-Paket: `studip_cli`, aufrufbar mit
`python -m studip_cli` (das ist der Rückfall für Tests ohne installiertes
Console-Script). Vertrag für den Build: Flags, Exit-Codes, Ausgabeformate und
Umgebungsvariablen werden hier wörtlich umgesetzt.

## Aufruf

```text
studip [--json] <unterkommando> [argumente] [--optionen]
studip --version
studip --help
```

`--json` ist ein globales Flag und darf auch hinter dem Unterkommando stehen.
`-h`/`--help` und `--version` enden immer mit Exit 0. Unbekannte
Unterkommandos oder Argumente enden mit Exit 2 und einer Usage-Meldung.

Es gibt keine schreibende Web-Aktion und deshalb auch kein `--confirm`.
`studip download` schreibt nur lokal.

## Unterkommandos

### `studip login`

```text
studip login [--json]
```

Fragt interaktiv nach den Werten, die nicht schon aus Env oder Config
vorhanden sind:

```text
Stud.IP-Adresse: <https://demo.studip.de>
Benutzer: <max.mustermann@example.invalid>
Passwort: <verdeckt per getpass>
```

`STUDIP_BASE_URL` hat Vorrang vor einer eingetippten Adresse. Sind Adresse,
Benutzer und Passwort per Env gesetzt, fragt der Befehl nichts ab (Agenten und
Fake-Server). Die Zugangsdaten werden gegen
`GET /jsonapi.php/v1/users/me` mit HTTP Basic geprüft. Erfolg gilt erst, wenn
die Antwort `data.id` und `data.attributes.formatted-name` oder
`data.attributes.username` enthält – nicht schon, wenn ein Cookie existiert.

Bei Erfolg werden Instanz und Benutzer in der Config und das Passwort im
Schlüsselbund (Rückfall: Datei mit 0600) gespeichert.

Textausgabe:

```text
Login erfolgreich als Max Mustermann
```

### `studip logout`

```text
studip logout [--json]
```

Löscht Sitzung, gespeichertes Passwort und Keyring-Eintrag. Ist nichts
gespeichert, endet der Befehl trotzdem mit Exit 0 (idempotent). Text:
`Nicht angemeldet.` oder `Abgemeldet.`

### `studip whoami`

```text
studip whoami [--json]
```

Lädt `GET /jsonapi.php/v1/users/me` mit den aufgelösten Zugangsdaten. Text:

```text
Angemeldet als Max Mustermann (max.mustermann@example.invalid)
Instanz: https://demo.studip.de
```

Fehlt der Login oder antwortet der Server mit 401/403, endet der Befehl mit
Exit 4 und dem Hinweis `Login fehlt – studip login ausführen`.

### `studip kurse [SUCHBEGRIFF]`

```text
studip kurse [SUCHBEGRIFF] [--semester SEMESTER] [--json]
```

- Mit Suchbegriff: `GET /jsonapi.php/v1/courses?filter[q]=<begriff>&filter[fields]=title_lecturer_number`,
  optional zusätzlich `filter[semester]=<semester>`.
- Ohne Suchbegriff: eigene Kurse über `GET /users/me/courses` (Rückfall:
  `GET /courses`), optional nach Semester gefiltert.
- Der Suchbegriff ist positional und freiwillig; es gibt keine Pflicht-Option.
- Mehrere Treffer sind ein normales Suchergebnis: alle werden nummeriert
  ausgegeben, Exit 0 (keine Auswahl nötig).

Textausgabe:

```text
1) Physik I: Mechanik (PHY-101)
2) Physik II: Elektrodynamik (PHY-201)
```

Keine Treffer: `Keine Kurse gefunden.` mit Exit 0. `--semester` nimmt den
Semesternamen oder die Semester-ID; unbekannte Semester sind ein Fehler der
Quelle (Exit 3).

### `studip dateien KURSNAME`

```text
studip dateien KURSNAME [--json]
```

Löst `KURSNAME` per Kurssuche auf (siehe „Kurs- und Dateiauflösung“). Danach:

- `GET /jsonapi.php/v1/courses/{id}/folders`
- `GET /jsonapi.php/v1/courses/{id}/file-refs`

Textausgabe (Ordner eingerückt, Dateien mit deutscher Größenangabe):

```text
Kurs: Physik I: Mechanik (PHY-101)
[Ordner] Materialien
  Skript.pdf (12,0 kB)
  Übungsblatt-01.pdf (345,0 kB)
[Ordner] Übungen
  Lösung-01.pdf (120,0 kB)
```

Ein leerer Kurs gibt `Keine Dateien gefunden.` mit Exit 0 aus.

### `studip download KURSNAME [DATEINAME]`

```text
studip download KURSNAME [DATEINAME] [--ziel ORDNER] [--ja] [--json]
```

- Löst Kurs und Datei per Name auf.
- Ohne `DATEINAME` werden alle Dateien des Kurses heruntergeladen.
- Ziel ist `--ziel ORDNER`, sonst `~/Downloads`. Das Verzeichnis wird bei
  Bedarf angelegt.
- Der Inhalt kommt von `GET /jsonapi.php/v1/file-refs/{id}/content`.
- Existiert die Zieldatei bereits, fragt das Tool im TTY:
  `Datei existiert bereits: … Überschreiben? [j/N]` (Default `N`).
  `--ja` überschreibt ohne Frage. Ohne TTY und ohne `--ja` wird die Datei
  nicht überschrieben und der Befehl endet mit Exit 1.
- Der Download ist keine schreibende Web-Aktion; es wird nichts hochgeladen,
  geändert oder gelöscht.

Textausgabe:

```text
Kurs: Physik I: Mechanik (PHY-101)
Datei: Skript.pdf (12,0 kB)
Gespeichert: Skript.pdf
```

Bei mehreren Dateien steht pro Datei eine `Gespeichert:`-Zeile. Bei Abbruch
durch `N`: `Abgebrochen, Datei nicht überschrieben.` mit Exit 1.

### `studip termine [KURSNAME]`

```text
studip termine [KURSNAME] [--json]
```

Ohne Kursname werden Termine der eigenen Kurse zusammengeführt; mit Kursname
wird der Kurs aufgelöst und `GET /courses/{id}/events` gelesen. Datumsabhängige
Auswahl nutzt das heutige Datum bzw. `STUDIP_HEUTE`. Text pro Termin:

```text
31.10.2026 14:00-16:00  Vorlesung (Hörsaal A)
```

Keine Termine: `Keine Termine gefunden.` mit Exit 0.

### `studip news [KURSNAME]`

```text
studip news [KURSNAME] [--json]
```

Ohne Kursname `GET /studip/news`, mit Kursname `GET /courses/{id}/news`. Text:

```text
31.10.2026  Ankündigungstitel
```

Keine News: `Keine Ankündigungen gefunden.` mit Exit 0.

## Kurs- und Dateiauflösung

- Suchbegriff ist der positional übergebene Name, nie eine ID.
- Genau ein Treffer oder genau ein exakter Titel-Treffer: direkt verwenden.
- Mehrere Treffer im TTY: nummerierte Liste `1) …`, Frage `Auswahl [1-N]:`,
  danach den gewählten Kurs verwenden.
- Mehrere Treffer ohne TTY: Liste ausgeben, Hinweis auf einen eindeutigeren
  Namen, Exit 2.
- Kein Treffer: `Kein Kurs gefunden: <name>` mit Exit 1.
- Dateinamen werden analog aufgelöst; ohne `DATEINAME` werden alle Dateien
  verwendet. Mehrere Teil-Treffer ohne TTY: Liste + Exit 2.

## Ausgabeformat

- Standard ist lesbarer Text, wenn stdout ein TTY ist.
- `--json` oder stdout kein TTY: genau **ein** JSON-Objekt auf stdout; Prompts
  und Fehlermeldungen gehen auf stderr. Kein Traceback.
- Bei `--json` steht auch bei Usage- und Laufzeitfehlern genau ein JSON-Objekt
  auf stdout:

```json
{"error":{"code":"login_required","message":"Login fehlt","next":"studip login"}}
```

Fehlercodes im JSON sind stabil: `usage`, `network`, `source`, `login_required`,
`login_failed`, `not_found`, `file_exists`, `aborted`, `internal`.

Beispiele für Erfolgs-JSON:

```json
{"kurse":[{"id":"phy-1","titel":"Physik I: Mechanik","nummer":"PHY-101","semester":"WiSe 2026/27"}]}
{"kurs":{"id":"phy-1","titel":"Physik I: Mechanik","nummer":"PHY-101"},"ordner":[{"name":"Materialien","dateien":[{"id":"fref-skript","name":"Skript.pdf","groesse":12288}]}]}
{"kurs":{"id":"phy-1","titel":"Physik I: Mechanik","nummer":"PHY-101"},"dateien":[{"name":"Skript.pdf","pfad":"/home/user/Downloads/Skript.pdf","groesse":12288}]}
{"base_url":"https://demo.studip.de","user":{"id":"user-example-1","username":"max.mustermann@example.invalid","formatted_name":"Max Mustermann"}}
{"termine":[{"id":"event-1","titel":"Vorlesung","start":"2026-10-31T14:00:00+01:00","ende":"2026-10-31T16:00:00+01:00","ort":"Hörsaal A"}]}
{"news":[{"id":"news-1","titel":"Ankündigung","datum":"2026-10-31T09:00:00+01:00"}]}
{"ok":true}
```

## Exit-Codes

| Code | Bedeutung |
|---:|---|
| 0 | Erfolg (auch „keine Treffer“) |
| 1 | Allgemeiner Fehler: kein Kurs/keine Datei, lokale Dateioperation, Überschreiben abgelehnt, Abbruch |
| 2 | Usage: unbekanntes Unterkommando/Argument, ungültiges `STUDIP_HEUTE`, mehrdeutiger Name ohne TTY, fehlende Angaben im nicht-interaktiven Login |
| 3 | Netz oder Quelle: DNS/Timeout/TLS, HTTP 5xx/429, ungültiges JSON, unerwartete Quelle |
| 4 | Login nötig oder fehlgeschlagen: keine Zugangsdaten, 401/403, abgelaufene Sitzung, falsches Passwort |
| 130 | Abbruch durch Strg+C |

HTTP 404 auf eine Kurs-/Dateiroute ist Exit 1 (`not_found`), HTTP 401/403 ist
Exit 4. Bei jedem Fehler nennt die Meldung den nächsten Schritt; ohne TTY und
ohne `--json` ist die Ausgabe weiterhin Text auf stderr.

## Umgebungsvariablen

| Variable | Wirkung |
|---|---|
| `STUDIP_BASE_URL` | Überschreibt die Instanz-URL (Fake-Server, Agenten). Höchste Priorität. |
| `STUDIP_URL` | Alternativer Name für die Instanz-URL; `STUDIP_BASE_URL` gewinnt. |
| `STUDIP_USER` | Benutzername; überschreibt die Config. |
| `STUDIP_PASSWORD` | Passwort; überschreibt Keyring/Config. Wird nie ausgegeben oder geloggt. |
| `STUDIP_HEUTE` | Nur für Tests und deterministische Ausgaben: heutiges Datum als `JJJJ-MM-TT`. Ungültige Werte → Exit 2. |
| `XDG_CONFIG_HOME` | Standard-Konfigurationsverzeichnis, falls gesetzt. |

Auflösung für die Instanz: `STUDIP_BASE_URL` → `STUDIP_URL` → Config →
interaktive Frage (nur `login`). URL wird um einen abschließenden `/` bereinigt
und muss `http://` oder `https://` sein.

## Config-Pfade

- Basisverzeichnis: `${XDG_CONFIG_HOME:-~/.config}/studip-cli/`
- `config.json` (0600): `{"base_url": "https://demo.studip.de", "user": "max.mustermann@example.invalid"}`
- Passwort: Keyring-Dienst `studip-cli`, Eintrag `<base_url>|<user>`; falls
  Keyring nicht verfügbar, `credentials.json` (0600) im selben Verzeichnis.
- Es werden nur die für Stud.IP nötigen Zugangsdaten gespeichert, keine Cookies
  fremder Identity-Provider. Passwörter erscheinen nie in `--json`, Logs,
  Fehlermeldungen oder Kommandozeilen-Flags.
- `logout` entfernt `config.json`, `credentials.json` und den Keyring-Eintrag,
  soweit vorhanden.

## Netzwerk

- Nur GET-Requests an die konfigurierte Instanz; Download ausschließlich über
  `/file-refs/{id}/content`.
- `Accept: application/vnd.api+json`, `User-Agent: studip-cli/<version>`.
- HTTP Basic nur an die konfigurierte Basis-URL. `http://` ist für lokale
  Fake-Server (`127.0.0.1`, `localhost`) erlaubt; für echte Instanzen wird
  `https://` erwartet.
- Keine automatischen Re-Logins bei abgelaufener Sitzung; stattdessen Exit 4
  mit Hinweis auf `studip login`.
