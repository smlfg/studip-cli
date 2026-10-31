# Anforderungen: studip-cli

## Zweck

`studip-cli` bringt die wichtigsten Stud.IP-Aufgaben in das Terminal. Es liest
Kurse, Dateien, Termine und Ankündigungen über die offizielle Stud.IP-JSON:API
(`/jsonapi.php/v1/`) und speichert Dateien lokal. Stud.IP ist die Lernplattform
vieler Hochschulen; das Tool funktioniert mit jeder Instanz, die die JSON:API
aktiviert hat (z. B. `https://studip.uni-goettingen.de` oder
`https://demo.studip.de`).

Das Tool ist für Menschen gedacht: Namen und Suchbegriffe statt IDs,
interaktiver Login, lesbare Terminal-Ausgabe und eine nummerierte Auswahl bei
mehreren Treffern.

## Nutzer-Aufgaben

1. **Anmelden und Identität prüfen.** `studip login` fragt Instanz, Benutzer
   und Passwort ab, prüft die Zugangsdaten gegen `/users/me` und speichert die
   Sitzung. `studip whoami` zeigt den angemeldeten Menschen, `studip logout`
   entfernt die gespeicherten Daten (idempotent).
2. **Kurse suchen.** `studip kurse physik` sucht Kurse über einen positional
   übergebenen Suchbegriff und zeigt Titel und Kursnummer.
3. **Dateien eines Kurses sehen.** `studip dateien "Physik I: Mechanik"` löst
   den Kursnamen auf und zeigt Ordner und Dateien eingerückt mit lesbarer Größe.
4. **Eine Datei herunterladen.** `studip download "Physik I: Mechanik"
   "Skript.pdf"` speichert die Datei lokal, standardmäßig unter `~/Downloads`.
   Vorhandene Dateien werden ohne Nachfrage nicht überschrieben.
5. **Termine und Ankündigungen lesen.** `studip termine [KURSNAME]` und
   `studip news [KURSNAME]` zeigen Termine bzw. News eines Kurses oder der
   eigenen Kurse.

Die abtippbaren Sitzungen stehen in [`docs/UX.md`](docs/UX.md) und sind die
Grundlage der Akzeptanztests unter `tests/acceptance/`.

## Nachfrage

Quelle: [`scratch/ref/NEXT20.md`](scratch/ref/NEXT20.md), Stand **30.10.2026**
(Nachfrage-Check nach dem demand-first-gate; gh-Suche, Glama,
modelcontextprotocol/servers-Issues, Web/Reddit und `curl` von der Box).

- Fazit für `studip-cli`: **GO**.
- Im Umfeld existieren Download-Tools wie `studip-sync` (★34), aber kein
  MCP-Server und kein vergleichbares Terminal-Tool mit Login, Kurssuche,
  Dateiliste und Download in einem Befehl (0 MCP).
- Nur Download-Tools sind belegt; das Tool bleibt deshalb bewusst auf Lesen
  und lokalen Download beschränkt.

## Datenquelle

- Offizielle Stud.IP-JSON:API unter `/jsonapi.php/v1/`, dokumentiert unter
  <https://docs.gitlab.studip.de/entwicklung/docs/jsonapi> und
  <https://hilfe.studip.de>.
- Authentifizierung per HTTP Basic gegen `GET /jsonapi.php/v1/users/me`.
- Lesende Endpunkte: `courses` (Suche mit `filter[q]`, `filter[semester]`),
  `users/me`, `users/{id}/courses`, `courses/{id}/folders`,
  `courses/{id}/file-refs`, `file-refs/{id}/content`, `courses/{id}/events`,
  `courses/{id}/news` sowie `semesters`.
- Die öffentliche Discovery unter `/jsonapi.php/v1/discovery` ist ohne Login
  lesbar und bestätigt die verwendeten Routen.
- Antworten sind JSON:API (`data`, `type`, `id`, `attributes`,
  `relationships`, `links`, Listen mit `meta.page`).

## Grenzen

- **Inoffiziell.** Das Tool ist kein Angebot der Stud.IP-Entwickler oder einer
  Hochschule. Es nutzt die dokumentierte JSON:API, kann sich aber mit
  Stud.IP-Versionen ändern.
- **Live nur lesend getestet.** Auf echten Instanzen wurden ausschließlich
  öffentliche GET-Requests und die Login-Seite geprüft; es gab und gibt keine
  Anmeldung auf echten Konten und keine schreibende Web-Aktion.
- **Keine schreibenden Aktionen.** Anlegen, Bearbeiten, Hochladen oder Löschen
  sind nicht Teil des Tools. Der einzige Schreibvorgang ist der lokale
  Download; vorhandene Dateien bleiben ohne Bestätigung unangetastet.
- **Keine Zugangsdaten im Repo.** Live-Login und authentifizierte Kurs-/Datei-
  antworten sind nicht belegbar; die Fixtures unter `tests/fixtures/ux/` sind
  anonymisiert und nach dem JSON:API-Schema synthetisch erzeugt.
- **Instanzabhängig.** Nicht jede Instanz aktiviert die JSON:API oder erlaubt
  Basic Auth. Rechte, Sichtbarkeit und Felder können je Kurs und Rolle
  abweichen; das Tool meldet 401/403/404 lesbar statt mit Traceback.
- **Kein MCP.** Es wird ausschließlich eine CLI gebaut.

## Qualitätsanforderungen

- Python ≥ 3.10, nur `argparse` plus `httpx`/`requests` (und ggf.
  `beautifulsoup4`); Console-Script heißt `studip`.
- `--version` und `--help` enden mit Exit 0; jeder Fehler hat eine klare
  Meldung mit nächstem Schritt und einen definierten Exit-Code.
- JSON nur mit `--json` oder wenn stdout kein TTY ist; Prompts gehen auf
  stderr. Keine Passwörter in Ausgaben, Logs, Flags oder Fixtures.
- Basis-URL über `STUDIP_BASE_URL` überschreibbar (Fake-Server, Agenten).
- Alle Sitzungen aus `docs/UX.md` haben mindestens einen Akzeptanztest.
