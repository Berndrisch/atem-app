import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import time

class AutoKindleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kindle Auto-Reader")
        
        # Fenstergröße und Position
        self.root.geometry("300x160")
        self.root.resizable(False, False)
        
        # Fenster immer im Vordergrund behalten, damit man schnell stoppen kann
        self.root.attributes('-topmost', True)
        
        self.is_running = False
        self.thread = None
        
        # UI Elemente aufbauen
        self.setup_ui()
        
    def setup_ui(self):
        # Intervall Eingabe
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=15)
        
        tk.Label(frame_top, text="Intervall (Sekunden):").pack(side=tk.LEFT, padx=5)
        
        self.interval_var = tk.StringVar(value="30")
        self.interval_entry = tk.Entry(frame_top, textvariable=self.interval_var, width=8, justify='center')
        self.interval_entry.pack(side=tk.LEFT)
        
        # Buttons
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(pady=10)
        
        self.start_btn = tk.Button(frame_buttons, text="▶ Start", command=self.start_autoturn, width=10)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(frame_buttons, text="■ Stopp", command=self.stop_autoturn, state=tk.DISABLED, width=10)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status Anzeige
        self.status_label = tk.Label(self.root, text="Status: Bereit", fg="gray")
        self.status_label.pack(side=tk.BOTTOM, pady=10)
        
    def start_autoturn(self):
        try:
            interval = int(self.interval_var.get())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Eingabefehler", "Bitte eine gültige Zahl größer als 0 eingeben.")
            return
            
        self.is_running = True
        
        # UI aktualisieren
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.interval_entry.config(state=tk.DISABLED)
        self.status_label.config(text=f"Status: Läuft (blättert alle {interval}s)", fg="green")
        
        # Hintergrund-Thread starten, damit die GUI nicht einfriert
        self.thread = threading.Thread(target=self.turn_loop, args=(interval,), daemon=True)
        self.thread.start()
        
    def stop_autoturn(self):
        self.is_running = False
        
        # UI aktualisieren
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.interval_entry.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Gestoppt", fg="red")
        
    def turn_loop(self, interval):
        while self.is_running:
            # Wir prüfen sekündlich, ob gestoppt wurde, 
            # anstatt `time.sleep(interval)` als Block zu nutzen.
            for _ in range(interval):
                if not self.is_running:
                    return
                time.sleep(1)
                
            if not self.is_running:
                break
                
            self.turn_page()
            
    def turn_page(self):
        # AppleScript-Befehl, um Kindle in den Vordergrund zu holen 
        # und die Pfeiltaste rechts (Key Code 124) zu drücken.
        applescript = """
        try
            tell application "Kindle" to activate
            delay 0.3
            tell application "System Events"
                key code 124
            end tell
        on error
            display dialog "Kindle App konnte nicht gefunden werden oder Berechtigung fehlt." buttons {"OK"} default button 1
        end try
        """
        try:
            # Führt das AppleScript unsichtbar im Hintergrund über das Terminal aus
            subprocess.run(['osascript', '-e', applescript], check=False)
        except Exception as e:
            print(f"Fehler: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    
    # Für Mac: Sorgt dafür, dass das Fenster im Vordergrund startet
    import os
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    
    app = AutoKindleApp(root)
    root.mainloop()
