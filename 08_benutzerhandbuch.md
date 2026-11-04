# Benutzerhandbuch (Eva – Einatmen*Verweilen*Ausatmen)

> **Baseline-Datum:** 2026-05-28 | **Verifiziert:** 2026-05-29 | **App-Version:** PWA v3 (Cache `eva-atem-app-v3`)

Dieses Handbuch beschreibt die Voraussetzungen, die Einrichtung, die Verwendung und die Funktionsweise der interaktiven Eva Atemübung.

---

## System-Voraussetzungen

### Für Anwender (Trainierende)

| Anforderung | Details |
|---|---|
| **Browser** | Google Chrome (≥90), Safari (≥15), Firefox (≥90), Edge (≥90), Opera (≥76) |
| **Betriebssysteme** | iOS (≥15), Android (≥10), macOS, Windows, Linux |
| **Browser-APIs** | Web Audio API, HTML5 Canvas 2D, Service Worker, localStorage |
| **Bildschirm** | Beliebige Auflösung (Retina-optimiert), Hoch- und Querformat |
| **Audio** | Lautsprecher oder Kopfhörer empfohlen |
| **Netzwerk** | Nur beim allerersten Laden erforderlich; danach voll offline-fähig |

### Für Entwickler (Lokales Setup & Testing)

| Anforderung | Details |
|---|---|
| **Lokaler Server** | Erforderlich für Service-Worker-Tests (HTTPS oder `localhost`) |
| **Python 3** | Für `python3 -m http.server` oder Hilfsskripte |
| **Node.js / npx** | Optional, für `npx serve .` |
| **Git** | Versionskontrolle |

---

## Installation & Erste Schritte

### Option 1: Lokales Ausführen zum Testen
Service Worker erfordern aus Sicherheitsgründen `localhost` oder HTTPS:

1. Öffnen Sie ein Terminal im Verzeichnis des Projekts.
2. Starten Sie einen lokalen Server:
   ```bash
   # Mit Python:
   python3 -m http.server 8000

   # Oder mit Node/npx:
   npx serve .
   ```
3. Öffnen Sie `http://localhost:8000` (Python) bzw. `http://localhost:3000` (serve) im Browser.

### Option 2: Als PWA auf dem Mobilgerät installieren
Die App ist als Progressive Web App konzipiert und kann offline installiert werden:

**iOS (Safari):**
1. Öffnen Sie die gehostete URL in **Safari** (kein anderer Browser).
2. Tippen Sie auf das **Teilen-Symbol** (Viereck mit Pfeil nach oben).
3. Wählen Sie **„Zum Home-Bildschirm"**.
4. Bestätigen Sie mit **„Hinzufügen"**.

**Android (Chrome):**
1. Öffnen Sie die gehostete URL in **Chrome**.
2. Tippen Sie auf das **Drei-Punkte-Menü** oben rechts.
3. Wählen Sie **„App installieren"** oder **„Zum Startbildschirm hinzufügen"**.

> Nach der Installation startet die App im Standalone-Modus (ohne Adressleiste) und funktioniert auch ohne Internetverbindung.

---

## Funktionsweise und Bedienung

### Die Atemübung durchführen

1. **Starten:** Drücken Sie den **Play-Button ▶** im unteren Bildschirmbereich.
2. **Atmen:** Folgen Sie der orangefarbenen **Atemkugel** auf der wellenförmigen Führungslinie:
   - 🔼 **Kugel steigt:** Einatmen
   - ⏸ **Kugel verweilt oben:** Luft anhalten (nur bei 4–7–8 und Box)
   - 🔽 **Kugel sinkt:** Ausatmen
   - ⏸ **Kugel verweilt unten:** Luft anhalten (nur bei Box)
3. **Orientierung:** Der eingeblendete Text unter der Kugel zeigt die aktuelle Phase an: *Einatmen*, *Ausatmen* oder *Halten*.
4. **Timer:** Die rotierende Sonne oben rechts zeigt die verbleibende Zeit an (z.B. `9:59`).
5. **Pausieren:** Tippen Sie erneut auf den Button (jetzt ⏸), um die Übung anzuhalten.
6. **Bildschirm:** Während einer aktiven Session wird der Bildschirm-Standby automatisch verhindert (Screen Wake Lock).

### Verfügbare Atemtechniken

| Technik | Rhythmus | Therapeutische Wirkung |
|---|---|---|
| **4–6** | 4s Ein → 6s Aus | Resonanzatmung, aktiviert den Parasympathikus |
| **4–7–8** | 4s Ein → 7s Halten → 8s Aus | Einschlafhilfe nach Dr. Andrew Weil |
| **Box** | 4s Ein → 4s Halten → 4s Aus → 4s Halten | Taktisches Atmen, Stressreduktion |
| **Eigene** | Frei wählbar (2–12s je Phase) | Individuell anpassbar |

### Einstellungen anpassen
Tippen Sie auf das **Zahnrad ⚙️** unten rechts. Ein Panel schiebt sich von unten auf:

| Einstellung | Beschreibung | Wertebereich |
|---|---|---|
| **Atemtechnik** | Wahl des Atem-Presets oder eigene Phasen | 4–6 / 4–7–8 / Box / Eigene |
| **Eigene Phasen** | Schieberegler für Einatmen, Halten oben, Ausatmen, Halten unten | 2–12s (Ein/Aus), 0–8s (Halten) |
| **Klangart** | Cello-Streicher oder Klangschale | Cello / Klangschale |
| **Schalen-Pitch** | Feintuning der Klangschale | −12 bis +12 Halbtöne |
| **Session-Dauer** | Übungsdauer | 5 / 10 / 15 / 20 Minuten |
| **Tonhöhe** | Transposition der Cello-Grundfrequenz | −12 bis +12 Halbtöne |
| **Haltephasen** | Klang während Haltephasen | Stille / Brummen (Drone) |
| **Ton am Hochpunkt** | Triangel-Ping beim Übergang zum Ausatmen | Aus / Ein, mit Tonhöhe −24 bis +24 |
| **Amplitude** | Wellenhöhe der Atemkurve | 15 % bis 58 % der Bildschirmhöhe |
| **Wochenziel** | Angestrebte Sessions pro Woche | 1 bis 14 |
| **Farben** | Farbwahl für Kugel, Linie, Hügel, Himmel | Freier Color-Picker |

### Statistiken & Verlauf
- **Abschluss-Dialog:** Nach Ablauf der Session zeigt eine Karte die Zusammenfassung: Dauer, Atemtechnik, geschätzte Atemzüge und den Wochenfortschritt.
- **Wochenfortschritt:** Oben links zeigt die Leiste mit grünen Punkten den Fortschritt (z.B. 🌱 3/5 diese Woche).
- **Wochenziel-Feier:** Wird das Ziel erreicht, erscheint ein Glückwunsch-Dialog mit Konfetti-Animation (einmalig pro Kalenderwoche).
- **Verlauf:** Über „Verlauf ansehen" wird ein Balkendiagramm der letzten 4 Kalenderwochen angezeigt.

---

## App-Updates
Die App aktualisiert sich über den Service Worker:
1. Bei jedem Laden prüft der Browser, ob ein neuer Service Worker verfügbar ist.
2. Ist ein Update vorhanden, erscheint oben ein orangefarbener Button: **„App aktualisieren!"**
3. Tippen Sie darauf – die App lädt sich mit der neuen Version neu.

---

## Fehlerbehebung (Troubleshooting)

### Ton ist nicht zu hören
- Prüfen Sie das **Lautsprecher-Symbol** oben rechts (🔊 = aktiv, 🔇 = stumm). Tippen Sie darauf zum Umschalten.
- **iOS/Safari:** Die Web Audio API erfordert eine direkte Benutzerinteraktion (Klick/Tap), bevor Ton abgespielt werden kann. Starten Sie die Übung immer über den Play-Button.
- Prüfen Sie die **System-Lautstärke** und den **Stummschalter** Ihres Geräts (Seitenschalter bei iPhones).

### App lässt sich nicht installieren (Home-Bildschirm)
- Verwenden Sie den **Standard-Browser** (Safari unter iOS, Chrome unter Android).
- In-App-Browser (Instagram, Facebook, etc.) unterstützen die PWA-Installation nicht.

### Daten sind verschwunden
- Session-Daten werden im Browser-`localStorage` gespeichert. Wird der Browser-Cache gelöscht oder das Gerät zurückgesetzt, gehen die Daten verloren.
- **Geplant:** Ein Export/Import-Feature zum Sichern der Übungshistorie (siehe Roadmap).

### Bildschirm wird dunkel während der Übung
- Die App nutzt die Screen Wake Lock API, um dies zu verhindern. Diese API ist in manchen älteren Browsern nicht verfügbar.
- **Workaround:** Stellen Sie die Bildschirm-Timeout-Zeit Ihres Geräts manuell auf einen höheren Wert.
