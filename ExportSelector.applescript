tell application "System Events"
    activate
    set dialogResult to display dialog "Wie möchtest du die Chrome-Tabs als PDF speichern?" buttons {"Abbrechen", "Exakt (Dauert länger)", "Schnell (Hintergrund)"} default button "Schnell (Hintergrund)" cancel button "Abbrechen" with title "Chrome Tabs als PDF speichern"
end tell

if button returned of dialogResult is "Schnell (Hintergrund)" then
    do shell script "nohup /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 '/Users/bernd/DOKUMENTE-local/__Eva/atem-app/save_chrome_tabs.py' > /dev/null 2>&1 &"
    
    tell application "System Events"
        activate
        display notification "Der Export wurde im Hintergrund gestartet." with title "PDF Export Schnell"
    end tell
else if button returned of dialogResult is "Exakt (Dauert länger)" then
    tell application "System Events"
        activate
        display alert "Achtung!" message "Der Export startet jetzt. Bitte berühre während des Exports NICHT die Maus oder Tastatur, bis alle Tabs geschlossen/bearbeitet wurden!" as warning
    end tell
    
    do shell script "osascript '/Users/bernd/DOKUMENTE-local/__Eva/atem-app/save_chrome_tabs_gui.applescript' > /dev/null 2>&1 &"
end if
