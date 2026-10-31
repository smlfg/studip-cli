# UX-Spec: studip

Diese Spec beschreibt die wichtigsten Aufgaben für `studip-cli` so, wie ein
Mensch sie im Terminal abtippt. Alle Kursnamen, IDs und Zugangsdaten sind
Beispieldaten; Mails enden auf `example.invalid`. Das Tool spricht die
offizielle Stud.IP-JSON:API unter `/jsonapi.php/v1/` an.

Grundsatz: `studip-cli` liest nur. Es gibt keine schreibende Web-Aktion und
deshalb auch keine `ux-formsteps`. Der einzige lokale Schreibvorgang ist der
Download in ein Zielverzeichnis; dabei wird ohne Nachfrage nichts überschrieben.

## Meta

```ux-meta
{"tool": "studip",
 "install": "pipx install git+https://github.com/smlfg/studip-cli",
 "base_url_env": "STUDIP_BASE_URL",
 "env": {"STUDIP_HEUTE": "2026-10-31"},
 "credential_env": ["STUDIP_USER", "STUDIP_PASSWORD"]}
```

`STUDIP_BASE_URL` überschreibt die Instanz-URL (für Fake-Server und Agenten).
`STUDIP_USER`/`STUDIP_PASSWORD` überschreiben die gespeicherten Zugangsdaten.
Für deterministische Termin-Ausgaben in Tests kann `STUDIP_HEUTE` auf
`JJJJ-MM-TT` gesetzt werden.

## Sitzungen

### Installation und erster Login

`studip login` fragt nach Instanz, Benutzer und Passwort. Das Passwort wird
verdeckt eingegeben und nicht angezeigt. Die Sitzung wird unter
`~/.config/studip-cli/` mit Rechten 0600 gespeichert (Passwort im
Schlüsselbund, falls verfügbar). `STUDIP_BASE_URL` gewinnt gegenüber der
eingetippten Adresse; so laufen die Gates gegen den Fake-Server. Die
Zugangsdaten hier sind erfunden.

```ux-session
$ pipx install git+https://github.com/smlfg/studip-cli
< studip
$ studip login
< Stud.IP-Adresse:
> https://demo.studip.de
< Benutzer:
> max.mustermann@example.invalid
< Passwort:
> geheim
< Login erfolgreich als Max Mustermann
! exit 0
```

### Kurse nach Namen suchen

Der Suchbegriff ist positional. Die Ausgabe zeigt Titel und Kursnummer, damit
ein Mensch ohne Nachschlagen weiterarbeiten kann. Mehrere Treffer werden im TTY
nummeriert angeboten; ohne TTY erscheint die Liste mit Exit-Code 2.

```ux-session
$ studip kurse physik
< 1) Physik I: Mechanik (PHY-101)
< 2) Physik II: Elektrodynamik (PHY-201)
! exit 0
```

### Dateien eines Kurses anzeigen

Der Kurs wird über seinen Namen aufgelöst. Ordner und Dateien erscheinen
eingerückt mit lesbarer Größe.

```ux-session
$ studip dateien "Physik I: Mechanik"
< Kurs: Physik I: Mechanik (PHY-101)
< [Ordner] Materialien
<   Skript.pdf (12,0 kB)
<   Übungsblatt-01.pdf (345,0 kB)
< [Ordner] Übungen
<   Lösung-01.pdf (120,0 kB)
! exit 0
```

### Eine Datei herunterladen

Ohne `--ziel` landet die Datei unter `~/Downloads`. Existiert die Datei bereits,
fragt das Tool im TTY vor dem Überschreiben nach; ohne TTY bricht es ab. Der
Download selbst ist eine lokale Dateioperation, keine schreibende Web-Aktion.

```ux-session
$ studip download "Physik I: Mechanik" "Skript.pdf"
< Kurs: Physik I: Mechanik (PHY-101)
< Datei: Skript.pdf (12,0 kB)
< Gespeichert: Skript.pdf
! exit 0
```

## Lesende Routen

Alle Requests der Sitzungen gegen den Fake-Server. Die Antworten sind
JSON:API-Ressourcen; die Kurs-/Dateidaten sind aus der öffentlichen
Discovery-Struktur abgeleitet und anonymisiert. Die Login-Antwort ist
synthetisch und im JSON mit `"synthetic": true` markiert, weil ohne echte
Zugangsdaten kein Live-Login stattfindet.

```ux-routes
[{"method":"GET","path":"/jsonapi.php/v1/users/me","response":"tests/fixtures/ux/login_erfolg.json","status":200,"content_type":"application/vnd.api+json; charset=utf-8"},
 {"method":"GET","path":"/jsonapi.php/v1/courses","query_contains":"filter%5Bq%5D","response":"tests/fixtures/ux/kurse_physik.json","status":200,"content_type":"application/vnd.api+json; charset=utf-8"},
 {"method":"GET","path":"/jsonapi.php/v1/courses/phy-1/folders","response":"tests/fixtures/ux/ordner_phy1.json","status":200,"content_type":"application/vnd.api+json; charset=utf-8"},
 {"method":"GET","path":"/jsonapi.php/v1/courses/phy-1/file-refs","response":"tests/fixtures/ux/dateien_phy1.json","status":200,"content_type":"application/vnd.api+json; charset=utf-8"},
 {"method":"GET","path":"/jsonapi.php/v1/file-refs/fref-skript/content","response":"tests/fixtures/ux/skript.pdf","status":200,"content_type":"application/pdf"}]
```

## Schreibende Aktion

Es gibt keine schreibende Web-Aktion. `studip download` schreibt nur lokal und
fragt vor dem Überschreiben im TTY nach `[j/N]`; ohne TTY und ohne `--ja`
bricht es ab. Deshalb enthält diese Spec bewusst keinen `ux-formsteps`-Block.
