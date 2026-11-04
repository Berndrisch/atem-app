# API-Schnittstellen und Datenverträge

> **Baseline-Datum:** 2026-05-28 | **Verifiziert:** 2026-05-29 | **Quellversion:** `index.htm` (1575 Zeilen), `sw.js` (57 Zeilen), `manifest.json` (21 Zeilen)

Dieses Dokument beschreibt die Schnittstellen, die lokale Datenspeicherung, die Browser-APIs und die Syntheseparameter der Eva Atemübung.

## Externe Web-APIs
- **Keine Server-APIs:** Die Anwendung kommuniziert nicht mit externen Server-Endpunkten. Alle Berechnungen, Zustandsänderungen und Audiosynthesen finden lokal im Client statt.
- **Einzige externe Ressource:** Google Fonts CDN (`fonts.googleapis.com`) für die Schriftart Quicksand (wird vom Service Worker gecacht).

---

## Verwendete Browser-APIs

| API | Zweck | Datei | Fallback-Strategie |
|---|---|---|---|
| **Canvas 2D API** | Rendering: Hintergrund, Kurve, Kugel, Sonne, Verlaufs-Diagramm | `index.htm` | Keine (Kern-Voraussetzung) |
| **Web Audio API** | Echtzeit-Audiosynthese (Cello, Klangschale, Ping, Drone) | `index.htm` | `webkitAudioContext` Fallback für Safari |
| **Service Worker API** | Offline-Caching, Update-Management | `sw.js`, `index.htm` | Feature-Detection (`'serviceWorker' in navigator`) |
| **Cache API** | Asset-Caching (Cache-First-Strategie) | `sw.js` | Netzwerk-Fallback |
| **Web Storage (localStorage)** | Session-Verlauf, Glückwunsch-Flags | `index.htm` | Try-Catch mit leerer Array-Rückgabe |
| **Screen Wake Lock API** | Verhindert Bildschirm-Standby während Session | `index.htm` | Feature-Detection + `try/catch` |
| **requestAnimationFrame** | 60fps-Animationsloop | `index.htm` | Keine (Kern-Voraussetzung) |
| **devicePixelRatio** | Retina/HiDPI-Support | `index.htm` | Fallback auf `1` |

---

## Lokale Zustandsspeicherung (Browser `localStorage`)

### 1. `eva_s` (Session-Protokolle)
- **Schlüssel:** `eva_s`
- **Wert:** Serialisiertes JSON-Array von Übungssitzungen.
- **Max. Größe:** Unbegrenzt (bis zum localStorage-Limit des Browsers, typisch 5–10 MB).
- **Datenstruktur:**
  ```typescript
  interface BreathingSession {
    date: string;       // ISO-Datumstring "YYYY-MM-DD" (via new Date().toISOString().split('T')[0])
    duration: number;   // Konfigurierte Session-Dauer in Sekunden (z.B. 300, 600, 900, 1200)
    pattern: string;    // Label des aktiven Presets: "4–6", "4–7–8", "Box" oder "Eigene"
  }
  ```
- **Beispiel:**
  ```json
  [
    { "date": "2026-05-28", "duration": 600, "pattern": "4–6" },
    { "date": "2026-05-27", "duration": 300, "pattern": "Box" }
  ]
  ```
- **Zugriffsmethoden:**
  - `loadSessions()` → `JSON.parse(localStorage.getItem('eva_s') || '[]')` mit Try-Catch.
  - `saveSessions(s)` → `localStorage.setItem('eva_s', JSON.stringify(s))`.

### 2. `eva_cg_[year]_[week]` (Glückwunsch-Flag)
- **Schlüssel:** Dynamischer String, z.B. `eva_cg_2026_22`
- **Wert:** `"1"`
- **Zweck:** Verhindert mehrfaches Anzeigen des Wochenziel-Glückwunsch-Dialogs in derselben Kalenderwoche.
- **Berechnung:** `'eva_cg_' + new Date().getFullYear() + '_' + weekNum(new Date())`

---

## Interne Datenstrukturen

### 1. Globales Zustandsobjekt `S`
Zentraler, nicht-persistierter In-Memory-State für die laufende Session:

```typescript
interface AppState {
  // Session-Steuerung
  running: boolean;         // Läuft die Session?
  sesTime: number;          // Verstrichene Zeit in Sekunden (hochzählend)
  sesDur: number;           // Konfigurierte Dauer in Sekunden (default: 600 = 10 min)
  breaths: number;          // Gezählte Atemzüge (inkrementiert um 0.5 pro Phase)
  ts: number | null;        // Letzter Timestamp für Delta-Time-Berechnung
  lastPhase: string | null; // Letzte Atemphase für Phasenwechsel-Erkennung

  // Atem-Timing
  bt: number;               // Gesamt-Atem-Timer (kumuliert, mod cycleLength)
  phases: BreathingPhase[];  // Aktive Phasenkonfiguration

  // Animation
  rot: number;              // Kugel-Rotationswinkel (Radianten)
  squish: number;           // Kugel-Verformungsfaktor (1.0 = Kreis)
  squishT: number;          // Definition ausstehend (im Code deklariert aber nicht aktiv genutzt)

  // Audio
  pitchShift: number;       // Tonhöhenverschiebung in Halbtönen (-12 bis +12)
  soundType: 'cello' | 'bowl';  // Aktive Klangart
  drone: boolean;           // Haltephasen-Brummen an/aus (default: false)
  ping: boolean;            // Hochpunkt-Ping an/aus (default: false)
  pingPitch: number;        // Ping-Tonhöhe in Halbtönen (-24 bis +24)
  bowlPitch: number;        // Klangschalen-Feintuning in Halbtönen (-12 bis +12)

  // Visuell
  amp: number;              // Wellenhöhe als Faktor (0.15 bis 0.58, default: 0.38)
  cBall: string;            // Hex-Farbe Kugel
  cLine: string;            // Hex-Farbe Linie
  cHill: string;            // Hex-Farbe Hügel
  cSky: string;             // Hex-Farbe Himmel
}
```

### 2. Phasen-Definition (`BreathingPhase`)
```typescript
interface BreathingPhase {
  phase: 'inhale' | 'hold_top' | 'exhale' | 'hold_bottom';
  duration: number; // Dauer in Sekunden (0.5er-Schritte möglich)
}
```

### 3. Atem-Presets (`PRESETS`)
```javascript
const PRESETS = [
  { label: '4–6',   phases: [{phase:'inhale',duration:4}, {phase:'exhale',duration:6}] },
  { label: '4–7–8', phases: [{phase:'inhale',duration:4}, {phase:'hold_top',duration:7}, {phase:'exhale',duration:8}] },
  { label: 'Box',   phases: [{phase:'inhale',duration:4}, {phase:'hold_top',duration:4}, {phase:'exhale',duration:4}, {phase:'hold_bottom',duration:4}] },
  { label: 'Eigene', phases: null }  // null = benutzerdefiniert über Slider
];
```

### 4. Dauer-Presets (`DURS`)
```javascript
const DURS = [5, 10, 15, 20]; // Minuten, default-Auswahl: Index 1 (10 min)
```

---

## Audio-Schnittstelle (`Audio`-Objekt)

### Architektur (Web Audio Graph)
```
Oszillatoren (8 Harmonische) ──→ OscGain (individuelle Amplitude)
                                    │
LFO (Vibrato 4.8 Hz) ──→ VibratoGain ──→ Osc1+Osc2 Frequency
                                    │
Noise (Buffer, Bandpass 900 Hz) ──→ NoiseGain (0.035)
                                    │
                              ┌─────┴──────┐
                              │ BiquadFilter │ (Lowpass 1200 Hz, Q: 0.8)
                              └─────┬──────┘
                                    │
                              ┌─────┴──────┐
                              │ breathGain  │ (dynamische Lautstärke 0-1)
                              └─────┬──────┘
                                    │
                              ┌─────┴──────┐
                              │ masterGain  │ (0.6 oder 0 bei Mute)
                              └─────┬──────┘
                                    │
                              AudioContext.destination
```

### Cello-Synthese (Harmonische)
| Oberton | Multiplikator | Amplitude | Wellenform | Vibrato |
|---|---|---|---|---|
| 1 (Grundton) | 1× | 0.55 | sawtooth | Ja |
| 2 | 2× | 0.42 | sine | Ja |
| 3 | 3× | 0.28 | sine | Nein |
| 4 | 4× | 0.18 | sine | Nein |
| 5 | 5× | 0.12 | sine | Nein |
| 6 | 6× | 0.08 | sine | Nein |
| 7 | 7× | 0.05 | sine | Nein |
| 8 | 8× | 0.03 | sine | Nein |

**Tonhöhen-Mapping (Atemphase → Frequenz):**
| Phase | Basisfrequenz | Note |
|---|---|---|
| `inhale` / `hold_bottom` | 146.83 Hz | D3 |
| `exhale` / `hold_top` | 97.99 Hz | G2 |

**Pitch-Formel:** `targetFreq = baseFreq × 2^(pitchShift/12)`

**Glissando:** `osc.frequency.setTargetAtTime(targetFreq * mult, time, 0.35)` — Zeitkonstante 350ms simuliert Cello-Griff.

### Klangschale (`Audio.playBowl()`)
| Partial | Multiplikator | Amplitude | Decay (s) | Pitch-Drift (Hz) | Attack (s) |
|---|---|---|---|---|---|
| Fundament | 1.0× | 1.0 | 34 | 0 | 0.06 |
| Körper | 2.76× | 0.6 | 22 | −1.5 | 0.04 |
| Bloom | 5.4× | 0.55 | 18 | +4.5 | 4.5 (!) |
| Anschlag | 8.93× | 0.5 | 7 | −2.0 | 0.02 |
| Zing | 14.34× | 0.25 | 3 | −6.0 | 0.01 |

**Basis:** 174 Hz (Healing Frequency), modifiziert durch `S.bowlPitch`.
**Schwebung:** Jeder Partial erhält einen eigenen LFO (0.5–2.0 Hz, zufällig) mit `gain: 1.0 + mult × 0.25`.

### Triangel-Ping (`Audio.playPing(pitchOffset)`)
- **Basisfrequenz:** 880 Hz (A5)
- **Wellenform:** Triangle
- **LFO:** 3.5 Hz Sine, Gain 6.0
- **Envelope:** Attack 40ms → Decay 2.5s (exponentiell)

### Lautstärke-Dynamik im Animationsloop
```javascript
// Innerhalb inhale/exhale: Sinus-Bogen
volSwell = Math.sin(progress * Math.PI);  // 0 → 1 → 0

// Haltephasen (hold_top / hold_bottom):
volSwell = S.drone ? 0.12 : 0;  // 12% oder Stille
```

### Methoden-Übersicht
| Methode | Signatur | Beschreibung |
|---|---|---|
| `init()` | `() → void` | Erstellt AudioContext, baut Synthese-Graph auf |
| `build()` | `() → void` | Instanziiert Oszillatoren, Filter, Rauschen |
| `update(vol, targetFreq)` | `(number, number) → void` | Setzt Lautstärke und Frequenz (Cello) |
| `setActive(on)` | `(boolean) → void` | Startet/stoppt die Tonausgabe |
| `setVolume(v)` | `(number) → void` | Master-Gain einstellen |
| `playBowl()` | `() → void` | Klangschale abspielen (One-Shot) |
| `playPing(pitchOffset)` | `(number) → void` | Triangel-Ping (One-Shot) |

---

## Screen Wake Lock API

```typescript
// Schnittstelle
requestWakeLock(): Promise<void>   // navigator.wakeLock.request('screen')
releaseWakeLock(): void            // wakeLock.release()

// Automatische Wiederherstellung bei Visibility-Change
document.addEventListener('visibilitychange', ...)  // Re-acquire wenn running + visible
```

---

## Service Worker Kommunikation (`sw.js` ↔ `index.htm`)

### Cache-Strategie: Cache-First
```
Request → Cache Match?
  ├─ Ja  → Cache Response
  └─ Nein → fetch(request)
```

### Gecachte Assets (Cache-Name: `eva-atem-app-v3`)
```javascript
['./','./index.htm','./manifest.json',
 'https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700&display=swap']
```

### Update-Protokoll
1. `registration.installing` → neuer SW gefunden.
2. `newWorker.state === 'installed'` + bestehender Controller → Update verfügbar.
3. UI zeigt `#update-btn`.
4. User klickt → `worker.postMessage('SKIP_WAITING')`.
5. SW empfängt Message → `self.skipWaiting()`.
6. `navigator.serviceWorker.controllerchange` → `window.location.reload()`.

---

## PWA-Manifest (`manifest.json`)

```json
{
  "name": "Eva Atemübung",
  "short_name": "Eva",
  "description": "Systemische Resilienzförderung durch geführte Atmung.",
  "start_url": "./index.html",
  "display": "standalone",
  "background_color": "#a8c8e8",
  "theme_color": "#7ec850",
  "icons": [
    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

> **Hinweis:** `start_url` verweist auf `./index.html`, die tatsächliche Datei heißt `index.htm`. Dies sollte bei einem zukünftigen Deployment abgeglichen werden.
