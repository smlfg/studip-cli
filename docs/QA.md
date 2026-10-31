# Pflicht-QA: studip

- Datum: 2026-10-31
- Prüfer: separater Prüfer (S5), nicht der Entwickler
- Version/Commit: `studip 0.1.0`, Repo-Commit `7a46cc9` (SHA von `src/studip_cli/cli.py`
  im pipx-Venv und im Repo identisch)
- Nachprüfung (S6): Fix `eb9bb06`; betroffenen Befehl erneut gegen den
  QA-Fake-Server ausgeführt (`scratch/qa/s6/`), danach UX-Gates erneut PASS
- Installation: `pipx install git+https://github.com/smlfg/studip-cli` in
  `scratch/pipx` (Protokoll `scratch/qa/pipx-install.log`); alle Aufrufe nur über
  `PATH=$PWD/scratch/pipx/bin:$PATH`
- Umgebung: Fake-Server gemäß `docs/UX.md` plus QA-Zusatzrouten
  (`scratch/qa/fake_run.py`); Blink-Abläufe im Pseudo-Terminal (`script -qc`);
  Belege unter `scratch/qa/s5/`
- Live-Zugriffe: nur lesende GETs auf öffentliche Seiten von
  https://demo.studip.de und https://studip.uni-goettingen.de (40-live-*),
  kein Login, keine schreibende Aktion

## Ergebnis

**35 / 35 OK.** Belege gekürzt; vollständige Protokolle unter `scratch/qa/s5/`,
Nachprüfung des Semesterfilters unter `scratch/qa/s6/`.

| Prüfung | Befehl | Erwartet | Ergebnis | Beleg (gekürzt) |
|---|---|---|---|---|
| Installation | PATH=…pipx/bin `studip --version` | `studip 0.1.0`, Datei im Venv = Repo-Datei | OK | 01-install.txt: Version + identische SHA256 |
| Hilfe | `studip --help`, `studip --version`, je Sub `--help` | Exit 0, verständliche Texte | OK | 02-help-main.log, 02-help-subs.txt (alle =0) |
| Login interaktiv | `studip login` (URL, Benutzer, Passwort) | Prompt-Reihenfolge, Meldung, Config 0600 | OK | 03-login-interaktiv.log, 03-config-perms.txt: `600` |
| Whoami | `studip whoami` | Name im TTY, kein JSON | OK | 04-whoami.log |
| Kurse | `studip kurse physik` | Treffer liste, Positionalsuche reicht | OK | 05-kurse.log, 09-kurse-json.out |
| Dateien | `studip dateien "Physik I: Mechanik"` | Ordner + Dateien, kein JSON | OK | 06-dateien.log |
| Download | `studip download "Physik I: Mechanik" "Skript.pdf"` | Datei im Zielordner | OK | 07-download-files.txt: `Skript.pdf 218 bytes` |
| JSON-Modus | `studip whoami/kurse/dateien --json` | valides JSON | OK | 08/09/10-*.jsoncheck.code = 0 |
| Termine | `STUDIP_HEUTE=2026-10-31 studip termine …` | Datum/Zeit/Ort lesbar, kein festes Datum nötig | OK | 11-termine.log |
| Termine JSON | `studip termine … --json` | valides JSON | OK | 12-termine-json.jsoncheck.code = 0 |
| News | `studip news "Physik I: Mechanik"` + `--json` | lesbar; JSON valide | OK | 13-news.log; 14-*.jsoncheck = 0 |
| Logout | `studip logout` | Meldung; Wiederholung ohne Absturz | OK | 15/16-logout*.log, Exit 0 |
| Login per Env | `STUDIP_USER=… STUDIP_PASSWORD=… studip login` | nur Adresse abgefragt | OK | 17-login-env.log |
| Login EOF | `studip login` < Strg+D | sauberes Ende, Exit 2, kein Traceback, nächster Schritt | OK | 18-login-eof.code = 2, Traceback-Scan 51 = nein |
| Login Strg+C | `studip login` + `^\3` | Exit 130, Hinweis statt Traceback | OK | 19-login-ctrl-c.log: `Fehler: Abgebrochen.` |
| Login falsch | env falsch, `studip login --json` | Exit 4, Fehler + nächster Schritt | OK | 20-login-falsch.out: `next: studip login erneut ausführen` |
| Server leere Antwort | Fake 200 ohne Nutzdaten, `studip login --json` | kein Absturz; Meldung verständlich | OK | 21-login-leer.code = 0, JSON valide |
| Leere Suche | `studip kurse nix` | freundliche Leer-Antwort, Exit 0 | OK | 22-kurse-leer.log: `Keine Kurse gefunden.` |
| Leerer Kurs | `studip dateien "Physik II: Elektrodynamik"` | `Keine Dateien gefunden.` | OK | 23-dateien-leer.log |
| Groß-/Kleinschreibung | `studip kurse PHYSIK`, `studip dateien "physik i: mechanik"` | Auflösung unabhängig von Schreibweise | OK | 24/25-*.log, Exit 0 |
| Semesterfilter mit Suche | `studip kurse physik --semester "WiSe 2026/27"` | nur Kurse aus WiSe 2026/27 | OK (nach Fix eb9bb06) | 27-kurse-semester-json.out enthält nur Physik I und III; Physik II (`SoSe 2027`) fehlt; Beleg `scratch/qa/s6/` |
| Mehrdeutig ohne TTY | `studip dateien Physik` (stdout kein TTY) | Exit 2, Fehler + nächster Schritt | OK | 29-*.out: `Mehrere Kurse gefunden … Eindeutigeren Kursnamen angeben` |
| mehrdeutig im TTY | `studip dateien Physik` + Auswahl `1` | Auswahlmenü, dann Trefferanzeige | OK | 30-kurs-mehrdeutig-tty.log |
| Download alle | `studip download "Physik I: Mechanik" --ziel …` | alle 3 Dateien | OK | 31-download-alle-files.txt |
| Download Teilname | `studip download … "01.pdf"` + Auswahl | nur Treffer mit „01.pdf“ | OK | 32-download-datei-files.txt (nur *-01.pdf) |
| Download Umlaut | `studip download … "übungsblatt"` | Ü im Namen löst auf | OK | 39-umlaut-files.txt: `Übungsblatt-01.pdf` |
| Überschreiben: Nein | Download auf bestehende Datei, Antwort `n` | Datei unverändert | OK | 33-download-sha.txt: sha before = after |
| Überschreiben: --ja | Download `--ja` auf bestehende Datei | ohne Nachfrage überschrieben | OK | 34-*.code = 0 |
| exists, kein TTY | erneut mit gleichem Ziel, kein TTY | Exit 1, JSON + nächster Schritt | OK | 35-*.out: `file_exists … --ja verwenden` |
| Netzfehler | `STUDIP_BASE_URL=http://127.0.0.1:9 studip kurse physik` | kein Traceback, Exit 3, Fehler + nächster Schritt | OK | 36-*.err: `Netzwerkfehler … Verbindung prüfen und erneut versuchen` |
| STUDIP_HEUTE ungültig | `STUDIP_HEUTE=31.10.2026 studip termine` | Exit 2, Format-Schema nennen | OK | 37-*.out: `STUDIP_HEUTE als JJJJ-MM-TT setzen` |
| Unbekanntes Kommando | `studip --json gibt-es-nicht` | Exit 2, Usage-Hinweis, JSON | OK | 38-*.out, jsoncheck = 0 |
| Live discovery | GET https://demo.studip.de/…/discovery, …goettingen… | 200, JSON:API | OK | 40-live-demo.txt: `demo discovery 200`, `goe discovery 200` |
| Live users/me ohne Auth | GET users/me (beide Instanzen) | 401 (kein Login-Versuch) | OK | 40-live-demo.txt: `users/me 401` |
| Live ohne Login an Tool | `studip whoami` / `studip kurse` gegen echte Instanz | Exit 4, `login_required` + nächster Schritt | OK | 41/42-*.out: `next: studip login ausführen` |
| Testsuite + Tracebacks | `pytest -q`, Scan über alle QA-Logs | Suite grün, kein Traceback irgendwo | OK | 50-pytest.txt: `38 passed`; 51-traceback-scan.txt: `nein` |

## Offene FAILs

Keine. Der frühere FAIL (Semesterfilter bei Suchbegriff) ist in `eb9bb06`
behoben: Der Filter wird jetzt zusätzlich clientseitig über Semester-ID und
Semestername angewendet. Nachprüfung mit demselben Befehl gegen den
QA-Fake-Server: Exit 0, nur WiSe-Kurse (`scratch/qa/s6/27-kurse-semester-json.out`).
UX-Gates danach erneut PASS (`scratch/qa/s6/ux-check.md`, `ux-session.md`).
