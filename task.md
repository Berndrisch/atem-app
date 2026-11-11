# Tasks (Eva – Einatmen*Verweilen*Ausatmen)

> **Letzte Aktualisierung:** 2026-11-11

Hier werden alle anstehenden und erledigten Projektschritte verwaltet.

---

## Phase 0: Initiales Setup & Audio/Visual Upgrades (Erledigt ✅)

- [x] Projekt-Repository angelegt und `.gitignore` konfiguriert
- [x] PWA-Grundstruktur erstellt (`index.htm`, `sw.js`, `manifest.json`, Icons)
- [x] Kernfunktionalität implementiert:
  - [x] Canvas-basiertes Rendering (Hintergrund, Sinuskurve, Atemkugel, Timer-Sonne)
  - [x] Atem-Presets (4–6, 4–7–8, Box, Eigene Phasen)
  - [x] Web Audio Synthese (Cello, Klangschale, Ping, Drone)
  - [x] Session-Tracking (localStorage, Wochenfortschritt, Glückwunsch-System)
  - [x] Settings-Panel (Bottom-Sheet mit allen Einstellungen)
  - [x] Verlaufs-Diagramm (4-Wochen-Balkendiagramm)
  - [x] Service Worker mit Update-Banner
  - [x] Screen Wake Lock für aktive Sessions
- [x] Audio- und Synthese-Überarbeitungen:
  - [x] Sinus-Sound: Reset in `setActive` korrigiert
  - [x] Cello-Sound: Tiefpassfilter von 650 Hz auf 1800 Hz geöffnet für wärmeren, lebendigeren Klang
  - [x] Flügelton / Arpeggio: 12 Obertöne mit FFT-Amplituden, Obertöne 3–6 mit Triangle-Textur für Körper und Tiefe
  - [x] Transposition: Filterresonanzen und Dämpfung in `_createGrandChain` dynamisch an `shiftFactor` gekoppelt
  - [x] Akkord-Tondifferenz: Am7 (Einatmen, hoch) / Gm7 (Ausatmen, tief)
- [x] Visuelle Szenen:
  - [x] Buddha-Szene: Bauchvolumen vergrößert (Grundradius 42, Expansion 38, angepasste Beine & Highlights)
- [x] Code-Inventur und Stack-Analyse durchgeführt (2026-05-28)
- [x] Baseline-Verifizierung: Zweiter Durchlauf bestätigt alle Einträge (2026-05-29)
- [x] Technische Baseline-Dokumentation erstellt und verifiziert:
  - [x] [04_frontend_ui.md](file:///Users/bernd/DOKUMENTE-local/__Eva/atem-app/04_frontend_ui.md) – UI-Komponenten, Design-Tokens, Rendering-Pipeline
  - [x] [05_api_contracts.md](file:///Users/bernd/DOKUMENTE-local/__Eva/atem-app/05_api_contracts.md) – Browser-APIs, Datenstructs, Audio-Synthese
  - [x] [08_benutzerhandbuch.md](file:///Users/bernd/DOKUMENTE-local/__Eva/atem-app/08_benutzerhandbuch.md) – Voraussetzungen, Installation, Bedienung
  - [x] [09_technische_aufzeichnung.md](file:///Users/bernd/DOKUMENTE-local/__Eva/atem-app/09_technische_aufzeichnung.md) – ADR 001: Stack-Begründung
  - [x] [10_incident_management.md](file:///Users/bernd/DOKUMENTE-local/__Eva/atem-app/10_incident_management.md) – Status: KEINE AKTIVEN INCIDENTS

---

## Phase 1: Nächste Entwicklungsschritte

- [ ] **Daten-Export/Import:** Implementierung eines Export/Import-Features für Session-Verlaufsdaten (JSON-Download/-Upload), um Datenverlust bei Browser-Cache-Bereinigung oder Gerätewechsel vorzubeugen
- [ ] **Manifest-Korrektur & Deployment-Härtung:** Abgleich der `start_url` in `manifest.json` (`./index.html` → `./index.htm`), Validierung der PWA-Installierbarkeit via Lighthouse-Audit, und Vorbereitung für statisches Hosting (GitHub Pages oder Firebase Hosting)
- [ ] **Nachtmodus (Dark Theme):** Alternatives Farbschema mit gedämpften, dunklen Tönen für abendliche Sessions – umschaltbar über das Settings-Panel, mit Persistierung der Auswahl im localStorage
