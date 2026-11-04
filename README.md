#atem-App

## HermesTime – lokale Mac-Zeitauswertung

Dieses Repository enthält zusätzlich einen kleinen lokalen macOS-Zeittracker:

- `mac_time_tracker.py` – erfasst aktive App/Fenstertitel/Browser-Domain und erzeugt Reports
- `HERMES_TIME.md` – Bedienung, Datenschutz-Hinweise und launchd-Setup

Schnellstart:

```bash
python3 mac_time_tracker.py init
python3 mac_time_tracker.py record
python3 mac_time_tracker.py report
python3 mac_time_tracker.py dashboard --open
```

Regelmäßige Erfassung:

```bash
python3 mac_time_tracker.py install-launch-agent
```
