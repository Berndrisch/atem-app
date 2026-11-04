# HermesTime – Mac-Zeittracking

HermesTime ist ein kleiner lokaler macOS-Tracker ohne externe Abhängigkeiten. Er erfasst regelmäßig die aktive App, optional den Fenstertitel und für Browser standardmäßig nur die Domain. Die Daten liegen lokal in SQLite unter:

```text
~/Library/Application Support/HermesTime/activity.sqlite
```

## Schnellstart

```bash
python3 mac_time_tracker.py init
python3 mac_time_tracker.py record
python3 mac_time_tracker.py report
python3 mac_time_tracker.py dashboard --open
```

Beim ersten Erfassen von App-/Fenstertiteln kann macOS nach Rechten fragen. Falls nur `Unbekannt` erfasst wird:

1. Systemeinstellungen öffnen
2. Datenschutz & Sicherheit → Bedienungshilfen
3. Terminal, Hermes oder die verwendete Shell-App erlauben

## Regelmäßige Erfassung per launchd

```bash
python3 mac_time_tracker.py install-launch-agent
```

Danach wird standardmäßig alle 60 Sekunden ein Sample gespeichert. Entfernen:

```bash
python3 mac_time_tracker.py uninstall-launch-agent
```

Logs liegen hier:

```text
~/Library/Application Support/HermesTime/launchd.log
~/Library/Application Support/HermesTime/launchd.err.log
```

## Konfiguration

Beim ersten `init` wird erzeugt:

```text
~/Library/Application Support/HermesTime/config.json
```

Wichtige Optionen:

- `sample_interval_seconds`: Sampling-Intervall, Default 60
- `max_gap_seconds`: maximale Dauer, die ein Sample im Bericht zählen darf, Default 180
- `idle_after_seconds`: ab wann Inaktivität als Pause zählt, Default 300
- `store_window_titles`: Fenstertitel speichern, Default true
- `browser_url_scope`: `domain`, `full` oder `off`; Default `domain`
- `categories`: Regeln für App-Namen, Domains und Fenstertitel-Keywords

Datenschutzfreundliche Empfehlung: `browser_url_scope` auf `domain` lassen. `full` speichert vollständige URLs und kann Suchanfragen oder private Pfade enthalten.

## Berichte

Tagesbericht:

```bash
python3 mac_time_tracker.py report --period day
```

Wochenbericht:

```bash
python3 mac_time_tracker.py report --period week
```

HTML-Dashboard erzeugen:

```bash
python3 mac_time_tracker.py dashboard --period day --open
```

## Hermes Cron optional

Wenn Hermes regelmäßig einen Bericht erstellen soll, kann ein Cron-Job nur lokal gespeichert werden oder über ein Gateway zugestellt werden. In dieser TUI-Sitzung werden Cron-Ergebnisse nicht live zurückgeliefert. Für lokale Nutzung reicht meist `launchd` plus manueller Report.

Beispiel für einen lokalen Skript-Report:

```bash
python3 /Users/bernd/DOKUMENTE-local/__Eva/atem-app/mac_time_tracker.py report --period day
```
