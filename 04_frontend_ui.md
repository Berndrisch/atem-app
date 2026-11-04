# Frontend-Dokumentation (UI & UX)

> **Baseline-Datum:** 2026-05-28 | **Verifiziert:** 2026-05-29 | **Quellversion:** `index.htm` (1575 Zeilen, 51.9 KB)

Dieses Dokument beschreibt die Benutzeroberfläche, das Styling, das Responsive Design und die UX-Konventionen der Eva Atemübung.

## Gefundene UI-Frameworks
- **Keine externen Frameworks:** Das Frontend ist als Single-Page-App (SPA) mit **Vanilla HTML5, CSS3 und modernem ES6+ JavaScript** implementiert. Es werden keine externen CSS-Frameworks (wie TailwindCSS, Bootstrap) oder JavaScript-Komponentenbibliotheken (wie React, Vue) verwendet.
- **Externe Abhängigkeiten:** Einzig die Google Font `Quicksand` wird als externe Ressource über CDN geladen.

---

## Design-Tokens

### Typografie
| Token | Wert | Kontext |
|---|---|---|
| **Primärschrift** | `'Quicksand', sans-serif` | Alle UI-Elemente, Buttons, Labels |
| **Gewichte** | 300 (Light), 400, 500, 600, 700 (Bold) | Light für Atemtext, Bold für Buttons |
| **Fallback** | System `sans-serif` | Browser-Standard |
| **Canvas-Font** | `'300 18px Quicksand'` | Atemphase-Label unter der Kugel |
| **Timer-Font** | `bold ${sr*0.44}px monospace` | Sonnen-Countdown |
| **Quelle** | Google Fonts CDN | `fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700` |

### Farbpalette (Standard-Konfiguration)
Alle Farben sind durch den Benutzer zur Laufzeit über `input[type=color]` anpassbar.

| Token | Hex | Zustand-Variable | Verwendung |
|---|---|---|---|
| **Himmel (Sky)** | `#a8c8e8` | `S.cSky` | Canvas-Hintergrund-Gradient (oben) |
| **Hügel (Hill)** | `#7ec850` | `S.cHill` | Sinuskurven-Füllung, Verlaufsbars, aktive Pills |
| **Atemkugel (Ball)** | `#ff6b35` | `S.cBall` | Radial-Gradient auf Canvas (mit ±60 Shade-Varianten) |
| **Führungslinie** | `#ffffff` | `S.cLine` | Sinuskurve mit Glow (`shadowBlur: 14`) |
| **Text dunkel** | `#3a6a2a` / `#4a7a3a` | — | Überschriften, Card-Titel |
| **Text gedämpft** | `#8a9a80` / `#8ab87a` | — | Statistiken, Section-Labels |
| **Akzent Grün** | `#7ec850` | — | Aktive Pills (`.pill.on`), Buttons |
| **Fortschritt aktiv** | `#5db83a` | — | Wochenpunkt `.dot.on` |
| **Fortschritt inaktiv** | `#d0e8c0` | — | Wochenpunkt `.dot` |
| **Panel-Hintergrund** | `rgba(248, 253, 245, 0.97)` | — | Settings-Panel Bottom-Sheet |
| **Overlay-Hintergrund** | `rgba(184, 212, 240, 0.95)` | — | Completion- & History-Screens |
| **Sonnenfarbe** | `#FFD700` / `#fffaaa` | — | Timer-Sonne (Radial-Gradient) |
| **Update-Button** | `#ff6b35` | — | SW-Update-Banner |
| **Konfetti** | `#ff6b35, #7ec850, #FFD700, #4a9e2f, #ff9a4a, #a8c8e8, #ff8c69` | — | 7-Farben-Palette |

### Farb-Hilfsfunktionen (JavaScript)
- **`shade(hex, n)`** – Verschiebt RGB-Kanäle um ±n (Aufhellung/Abdunklung).
- **`hexToRgba(hex, a)`** – Konvertiert Hex-Farbe zu RGBA-String.

### Glassmorphism & Transluzenz
| Element | Hintergrund | Blur | Schatten |
|---|---|---|---|
| Sound-Button | `rgba(255,255,255,0.82)` | — | `0 2px 10px rgba(0,0,0,0.1)` |
| Week-Bar | `rgba(255,255,255,0.82)` | `blur(10px)` | `0 2px 12px rgba(0,0,0,0.08)` |
| Settings-Panel | `rgba(248,253,245,0.97)` | `blur(14px)` | `0 -4px 30px rgba(0,0,0,0.1)` |
| Start-Button | `rgba(255,255,255,0.92)` | — | `0 4px 20px rgba(0,0,0,0.14)` |

---

## Layout & Responsivität

### Architektur (Zwei-Schicht-Rendering)
1. **Canvas-Schicht (`<canvas id="c">`):** Fullscreen, `position: fixed`, rendert Hintergrund, Sinuskurve, Hügel, Atemkugel, Atemtext und Timer-Sonne via 2D-Context.
2. **UI-Overlay (`<div id="ui">`):** Fixiert über dem Canvas mit `pointer-events: none`. Nur interaktive Elemente (Buttons, Panels) aktivieren `pointer-events: auto`.

### Pixel-Ratio-Handling (Retina-Support)
```javascript
DPR = window.devicePixelRatio || 1;
canvas.width = W * DPR; canvas.height = H * DPR;
canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
ctx.scale(DPR, DPR);
```
- Reagiert auf `window.resize` Events.
- Koordinaten werden logisch in CSS-Pixeln berechnet, physisch in Hardware-Pixeln gerendert.

### Mobile-Optimierungen
- `user-scalable=no` verhindert Zoom-Gesten.
- `touch-action: manipulation` unterdrückt Doppel-Tap-Zoom.
- `-webkit-tap-highlight-color: transparent` entfernt Touch-Highlight auf iOS.
- `apple-mobile-web-app-capable: yes` erlaubt Standalone-Modus auf iOS.
- `apple-mobile-web-app-status-bar-style: black-translucent` für transparente Statusleiste.

---

## UI-Komponenten

### 1. Wochenfortschritt-Leiste (`#week-bar`)
- **Position:** Links oben, abgerundet (`border-radius: 20px`).
- **Inhalt:** Emoji 🌱 + `{wc}/{wg} diese Woche` + Fortschrittspunkte.
- **Dynamik:** `updateWeekBar()` aktualisiert Punkte und Zähler aus `localStorage`.
- **Limit:** Maximal 10 Dots im Week-Bar, 12 Dots in der Completion-Card.

### 2. Aktions-Buttons
| Button | ID | Position | Funktion |
|---|---|---|---|
| **Start/Pause** | `#start-btn` | Unten Mitte (`bottom: 90px`) | Toggelt `S.running`, wechselt ▶/⏸ |
| **Settings** | `#settings-toggle` | Unten rechts (`bottom: 22px`) | Öffnet/schließt Settings-Panel |
| **Sound** | `#sound-btn` | Oben rechts (`top: 20px`) | Toggelt Mute (🔊/🔇), setzt Master Gain |
| **Update** | `#update-btn` | Oben Mitte | SW-Update-Banner, default `display: none` |

### 3. Einstellungs-Panel (`#settings-panel`)
- **Typ:** Bottom-Sheet mit Drag-Handle (`.handle`).
- **Animation:** `transform: translateY(100%)` → `translateY(0)` mit `cubic-bezier(.4, 0, .2, 1)` über 380ms.
- **Scrollbar:** `overflow-y: auto`, `max-height: 78vh`.
- **Schließ-Logik:** Klick außerhalb des Panels schließt es (Event-Listener auf `#ui`).

**Enthaltene Sektionen:**

| Sektion | Steuerelemente | State-Variable |
|---|---|---|
| **Atemtechnik** | 4 Pills (4–6, 4–7–8, Box, Eigene) | `PRESETS[]`, `activeP` |
| **Eigene Phasen** | 4 Range-Slider (Ein 2–12s, Halten 0–8s, Aus 2–12s, Halten 0–8s) | `S.phases[]` |
| **Klangart** | 2 Pills (Cello, Klangschale) | `S.soundType` |
| **Schalen-Pitch** | Range-Slider (−12 bis +12, Step 0.1) | `S.bowlPitch` |
| **Session-Dauer** | 4 Pills (5, 10, 15, 20 min) | `S.sesDur`, `activeD` |
| **Klangfarbe** | Range-Slider (−12 bis +12 Halbtöne) | `S.pitchShift` |
| **Haltephasen** | 2 Pills (Stille, Brummen) | `S.drone` |
| **Ton am Hochpunkt** | 2 Pills (Aus, Ein) + Range-Slider (−24 bis +24) | `S.ping`, `S.pingPitch` |
| **Amplitude** | Range-Slider (15–58%) | `S.amp` |
| **Wochenziel** | Range-Slider (1–14 Sessions/Woche) | via `#p-wg` |
| **Farben** | 4 Color-Picker (Kugel, Linie, Hügel, Himmel) | `S.cBall`, `S.cLine`, `S.cHill`, `S.cSky` |

### 4. Canvas-Rendering-Pipeline (Zeichenreihenfolge)
Jeder Frame in `requestAnimationFrame(loop)` zeichnet in folgender Reihenfolge:
1. **`drawBg()`** – Linearer Gradient (Sky → Sky+25 shade).
2. **`drawSun()`** – Timer-Sonne (8 rotierende Strahlen, Radial-Gradient, Countdown-Text).
3. **`drawHills()`** – Sinuskurven-Füllung unterhalb der Atemlinie (3-Stufen-Gradient).
4. **`drawCurve()`** – Weiße Führungslinie mit Glow-Effekt (`shadowBlur: 14`).
5. **`drawBall()`** – Atemkugel mit Radial-Gradient, Highlight, Kreuz-Rotation und Squish-Effekt.
6. **`drawBreathText()`** – Phasen-Label unterhalb/oberhalb der Kugel.

### 5. Atemkugel-Animation (Ball Physics)
- **Position:** Fixiert bei `x = W * 0.30`, `y` folgt der Atemkurve.
- **Squish-Deformation:** `ctx.scale(2 - sq, sq)` – streckt horizontal und staucht vertikal beim Einatmen.
- **Rotation:** Permanente Drehung basierend auf `S.rot += spd * dt / r`.
- **Kreuz-Overlay:** Zwei Linien (vertikal + horizontal) rotieren mit dem Ball.
- **Schatten:** `shadowBlur: 16`, `shadowOffsetY: 5`.

### 6. Easing-Funktion
```javascript
const ease = t => (1 - Math.cos(t * Math.PI)) / 2;
```
Cosinus-basiertes Ease-In-Out für butterweiche Übergänge der Atemkurve.

### 7. Abschluss-Bildschirm (`#completion`)
- Vollflächiges Overlay mit zentrierter Card (`.card`).
- **Eingangs-Animation:** `@keyframes card-in` – `scale(0.85)` → `scale(1)` mit `cubic-bezier(.175, .885, .32, 1.275)` (Overshoot-Bounce).
- Zeigt: Dauer, Atemtechnik, geschätzte Atemzüge, Wochenfortschritt mit Dots.
- Buttons: „Neue Session" (`.primary`) und „Verlauf ansehen" (`.secondary`).

### 8. Verlaufs-Modal (`#history`)
- Balkendiagramm auf `<canvas id="hc">` (280×150px).
- Zeigt die letzten 4 Kalenderwochen mit KW-Label.
- Horizontale Hilfslinien bei 25%, 50%, 75%, 100%.
- Verwendet `roundRect` mit Fallback auf `rect` für ältere Browser.

### 9. Glückwunsch-Dialog (`#congrats`)
- Zentriertes Toast-Element mit `transform: scale(0)` → `scale(1)`.
- Erscheint einmalig pro Kalenderwoche wenn `weekCount >= weekGoal`.
- Trigger: 300ms Delay nach Session-Ende oder 800ms nach App-Load.

### 10. Konfetti-System (`#confetti`)
- Spawnt 40 DOM-Elemente (`.cp`) mit zufälliger Größe (5–14px), Farbe, Form (Kreis/Rechteck).
- CSS-Animation `@keyframes fall`: `translateY(110vh) rotate(720deg)`, Dauer 2–4s.
- Auto-Cleanup nach 4000ms via `setTimeout`.

### 11. Service-Worker Update-Banner (`#update-btn`)
- Standardmäßig unsichtbar (`display: none`).
- Wird sichtbar wenn ein neuer SW im `installed`-Zustand wartet.
- Klick sendet `SKIP_WAITING` an den wartenden Worker, löst `controllerchange` → Page-Reload aus.
