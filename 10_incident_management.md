# Incident Management (Vorfallsdokumentation)

> **Baseline-Datum:** 2026-05-28 | **Verifiziert:** 2026-05-29

Dieses Dokument dient der Protokollierung und Nachverfolgung von Systemausfällen, kritischen Fehlern und Service-Einschränkungen im Projekt "Eva – Einatmen*Verweilen*Ausatmen".

---

## Aktueller Systemstatus

**Status: 🟢 [KEINE AKTIVEN INCIDENTS]**

| Metrik | Wert |
|---|---|
| Aktive Incidents | 0 |
| Offene Warnungen | 0 |
| Letzte Prüfung | 2026-05-29 (Verifizierung, zweiter Durchlauf) |

---

## Bekannte Einschränkungen (Non-Incidents)

Die folgenden Punkte wurden bei der Baseline-Analyse identifiziert. Sie stellen **keine akuten Vorfälle** dar, sollten aber bei der Weiterentwicklung beachtet werden:

| ID | Kategorie | Beschreibung | Schweregrad | Status |
|---|---|---|---|---|
| OBS-001 | Konfiguration | `manifest.json` verweist auf `start_url: "./index.html"`, die Datei heißt aber `index.htm`. Kann bei strikten PWA-Installationen zu Problemen führen. | Niedrig | Offen |
| OBS-002 | Datensicherheit | Keine Export/Import-Funktion für Session-Daten in `localStorage`. Bei Cache-Löschung gehen Trainingsdaten unwiederbringlich verloren. | Mittel | Geplant |
| OBS-003 | Kompatibilität | `CanvasRenderingContext2D.roundRect()` hat einen Fallback auf `rect()`, ist aber in älteren Browsern (< Chrome 99, < Safari 15.4) nicht verfügbar. | Niedrig | Mitigiert |

---

## Vorfalls-Historie

*Bisher wurden keine Incident-Tickets erfasst.*

---

## Eskalationsmatrix

| Schweregrad | Reaktionszeit | Verantwortlich |
|---|---|---|
| **Kritisch** (App nicht nutzbar) | < 4 Stunden | Projektleiter |
| **Hoch** (Kernfunktion eingeschränkt) | < 24 Stunden | Entwickler |
| **Mittel** (Feature eingeschränkt) | < 1 Woche | Entwickler |
| **Niedrig** (Kosmetisch/Edge-Case) | Nächstes Release | Backlog |

---

## Incident-Template

Für zukünftige Vorfälle folgendes Format verwenden:

```markdown
### INC-XXX: [Kurzbeschreibung]
- **Datum:** YYYY-MM-DD HH:MM
- **Schweregrad:** Kritisch / Hoch / Mittel / Niedrig
- **Betroffene Komponente:** [z.B. Audio, Canvas, Service Worker, localStorage]
- **Symptom:** [Was wurde beobachtet?]
- **Ursache:** [Root Cause, falls bekannt]
- **Maßnahmen:** [Was wurde unternommen?]
- **Status:** Offen / In Bearbeitung / Gelöst
- **Gelöst am:** YYYY-MM-DD
```
