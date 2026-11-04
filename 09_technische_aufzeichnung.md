# Technische Aufzeichnung (Architecture Decision Records)

> **Baseline-Datum:** 2026-05-28 | **Verifiziert:** 2026-05-29

Dieses Dokument dokumentiert die wesentlichen architektonischen Entscheidungen im Projekt "Eva – Einatmen*Verweilen*Ausatmen".

---

## ADR 001: Initiales System-Setup und Stack-Begründung

### Status
Akzeptiert (Accepted) — 2026-05-28

### Kontext
Das Projekt "Eva Atemübung" (EVA-APP) soll als vollkommen eigenständige, mobile und webbasierte Anwendung zur geführten Atemregulierung (Resonanzatmung, Stressabbau, Resilienzförderung) dienen. Folgende Anforderungen bestehen an die Software-Architektur:

1. **Verfügbarkeit & Plattformunabhängigkeit:** Die Anwendung muss plattformübergreifend (iOS, Android, macOS, Windows) funktionieren, idealerweise ohne App-Store-Freigabeprozesse.
2. **Offline-Fähigkeit:** Die Anwendung muss nach dem ersten Aufruf vollständig offline funktionieren (Flugzeug, Natur, Funklöcher).
3. **Flüssige Animationen und zeitkritische Audio-Wiedergabe:** Visuelle Signale (Atmungskugel, Kurve) und Audiosignale müssen exakt synchronisiert sein. Töne müssen latenzfrei auf Phasenwechsel reagieren.
4. **Schlanke Codebase & keine Hosting-Kosten:** Rein statisches Deployment ohne Server-Backend.
5. **Datenschutz:** Trainingsdaten verbleiben zu 100 % lokal auf dem Endgerät. Keine Registrierung, kein Login, keine externen Tracking-Dienste.

### Entscheidung
Progressive Web App (PWA) auf Basis nativer Web-Technologien:

#### 1. Frontend-Architektur (Single-Page-App in einer Datei)
- Die gesamte App wird als monolithische SPA in `index.htm` entwickelt (1575 Zeilen, 51.9 KB).
- HTML-Struktur, CSS (inline `<style>`) und JavaScript (inline `<script>`) in einer einzigen Datei.
- **Rendering:** Nativer HTML5 Canvas 2D API für alle visuellen Elemente (Hintergrund, Sinuskurve, Atemkugel, Timer-Sonne, Verlaufs-Diagramm).
- **Rationale:** Canvas ermöglicht stabile 60fps-Animationen, präzise Geometrieberechnungen und hardwarebeschleunigte Retina-Darstellung (`devicePixelRatio`-Skalierung) ohne DOM-Overhead.

#### 2. Echtzeit-Audiosynthese (Web Audio API)
Statt vorgefertigter Audiodateien (MP3/WAV) wird der Ton direkt im Client synthetisiert:
- **Cello:** 8 Harmonische (Sägezahn + Sinus-Obertöne), LFO-Vibrato (4.8 Hz), Lowpass-Filter (1200 Hz), Bow-Noise (Bandpass-gefiltertes Rauschen).
- **Klangschale:** 5 sinusförmige Partialtöne mit individuellem exponentiellen Decay, Frequenzdrift und Schwebung (Beating). Basis: 174 Hz (Healing Frequency).
- **Ping:** Triangle-Oszillator bei 880 Hz (A5) mit LFO-Vibrato.
- **Drone:** Leises Grundbrummen (12 % Amplitude) während Haltephasen.
- **Rationale:** Eliminiert Ladezeiten, ermöglicht stufenlose Tonhöhen-Transposition und phasen-synchrone Lautstärke-Dynamik.

#### 3. Offline-Support (Service Worker & Manifest)
- **`sw.js`** (57 Zeilen): Cache-First-Strategie, registriert bei `install` alle Kern-Assets inklusive Google Fonts CDN-URL.
- **`manifest.json`**: Deklariert die App als installierbare PWA im `standalone`-Modus.
- **Update-Mechanismus:** Automatische Erkennung neuer SW-Versionen, UI-Banner „App aktualisieren!", `SKIP_WAITING`-Message-Protokoll mit Page-Reload.

#### 4. Datenhaltung (Web Storage)
- Session-Historie als JSON-Array in `localStorage` (`eva_s`).
- Glückwunsch-Flags pro Kalenderwoche (`eva_cg_YYYY_WW`).
- **Rationale:** Kein Backend, kein Account, keine Netzwerk-Abhängigkeit. Datenschutzkonform by Design.

#### 5. Screen Wake Lock API
- Verhindert Bildschirm-Standby während aktiver Sessions.
- Feature-Detection mit Fallback (kein Fehler wenn nicht verfügbar).
- Automatische Re-Acquisition bei Visibility-Change (Tab-Wechsel zurück).

### Code-Inventur (Dateibestand)

#### Kern-Anwendung (PWA)
| Datei | Typ | Größe | Beschreibung |
|---|---|---|---|
| `index.htm` | HTML/CSS/JS | 51.9 KB (1575 Zeilen) | Monolithische SPA mit Canvas-Rendering und Web Audio |
| `sw.js` | JavaScript | 1.7 KB (57 Zeilen) | Service Worker (Cache-First, Update-Management) |
| `manifest.json` | JSON | 453 B (21 Zeilen) | PWA-Manifest (Standalone, Icons) |
| `icon-192.png` | PNG | 47 KB | App-Icon (192×192) |
| `icon-512.png` | PNG | 237 KB | App-Icon (512×512) |

#### Hilfsskripte (nicht Teil der PWA-Laufzeit)
| Datei | Sprache | Größe | Beschreibung |
|---|---|---|---|
| `save_chrome_tabs.py` | Python 3 | 12.2 KB (301 Zeilen) | Exportiert alle Chrome-Tabs als PDF mit Metadaten-Extraktion und HTML-Übersicht |
| `auto_kindle.py` | Python 3 | 4.4 KB (123 Zeilen) | Automatisiertes Kindle-Blättern via tkinter-GUI und AppleScript |
| `ExportSelector.applescript` | AppleScript | 1.2 KB (21 Zeilen) | Dialog zur Auswahl des Export-Modus (Schnell/Exakt) |
| `save_chrome_tabs_gui.applescript` | AppleScript | 2.1 KB (52 Zeilen) | GUI-Scripting-Variante des Chrome-Tab-Exports (Cmd+P Simulation) |

#### Dokumentation
| Datei | Typ | Beschreibung |
|---|---|---|
| `04_frontend_ui.md` | Markdown | Frontend-Dokumentation (UI & UX) |
| `05_api_contracts.md` | Markdown | API-Schnittstellen und Datenverträge |
| `08_benutzerhandbuch.md` | Markdown | Benutzerhandbuch |
| `09_technische_aufzeichnung.md` | Markdown | Diese Datei (ADRs) |
| `10_incident_management.md` | Markdown | Incident-Management-Protokoll |
| `task.md` | Markdown | Aufgaben-Tracking |

#### Sonstige
| Datei | Beschreibung |
|---|---|
| `.gitignore` | Git-Ignorierregeln (10 Bytes) |
| `.git/` | Git-Repository |

### Technologie-Stack (Zusammenfassung)

| Schicht | Technologie | Version/Standard |
|---|---|---|
| **Markup** | HTML5 | Living Standard |
| **Styling** | CSS3 (inline) | Inkl. `backdrop-filter`, `inset`, CSS Custom Properties |
| **Logik** | ES6+ JavaScript (inline) | Template Literals, Arrow Functions, Destructuring, `async/await` |
| **Rendering** | Canvas 2D API | `CanvasRenderingContext2D`, `roundRect` (mit Fallback) |
| **Audio** | Web Audio API | `AudioContext`, `OscillatorNode`, `BiquadFilterNode` |
| **Offline** | Service Worker + Cache API | Cache-First-Strategie |
| **Installierbarkeit** | PWA-Manifest | `display: standalone` |
| **Persistenz** | Web Storage (localStorage) | JSON-serialisiert |
| **Bildschirm** | Screen Wake Lock API | Feature-detected |
| **Typografie** | Google Fonts | Quicksand (300–700) |
| **Hilfsskripte** | Python 3 + AppleScript | macOS-spezifisch |

### Konsequenzen

#### Vorteile
- **Keine Betriebskosten:** Kostenfreies statisches Webhosting (GitHub Pages, Firebase Hosting, Netlify) reicht aus.
- **Extreme Portabilität:** Läuft auf jedem Gerät mit modernem Webbrowser.
- **Sofortige Installation:** "Zum Startbildschirm hinzufügen" — kein App Store nötig.
- **Perfekte Offline-Funktion:** Nach dem ersten Laden autark im Flugmodus.
- **Maximale Privatsphäre:** Zero-Trust-Backend, 100 % lokale Datenhaltung.
- **Flüssiges Feedback:** Latenzfreie Tonausgabe und butterweiche 60fps-Animationen durch direkte Hardwarebeschleunigung.
- **Minimale Angriffsfläche:** Keine Server-seitigen Angriffsvektoren, keine Authentifizierung, keine Datenbank.

#### Nachteile
- **Eingeschränkte Gerätesynchronisation:** Keine automatische Cross-Device-Synchronisation ohne Cloud-Backend.
- **Abhängigkeit vom Browser-Cache:** Bei Cache-Löschung oder Geräte-Reset gehen die localStorage-Daten verloren. (Export/Import ist als zukünftiges Feature geplant.)
- **Geringere Sichtbarkeit:** PWAs sind nicht in offiziellen App-Stores gelistet (außer über TWA/PWA-Builder).
- **Monolithische Dateistruktur:** Alle Logik in einer Datei erschwert bei wachsender Komplexität das Refactoring. (Aktuell bei 1575 Zeilen noch gut beherrschbar.)
- **Manifest-Inkonsistenz:** `start_url: "./index.html"` weicht vom tatsächlichen Dateinamen `index.htm` ab.
