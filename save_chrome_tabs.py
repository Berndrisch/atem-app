#!/usr/bin/env python3
import subprocess
import os
import re
import urllib.parse
import urllib.request
import json
from datetime import datetime

# Pfad zum Download-Ordner
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/Chrome_Tabs_PDFs")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Chrome-Pfad auf dem Mac
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DATABASE_FILE = os.path.join(DOWNLOAD_DIR, "datenbank.json")

def load_database():
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_database(entries):
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=4)

def get_chrome_tabs():
    applescript = """
    tell application "Google Chrome"
        set outString to ""
        repeat with w in windows
            repeat with t in tabs of w
                set outString to outString & (URL of t) & "|||" & (title of t) & "||||"
            end repeat
        end repeat
        return outString
    end tell
    """
    
    result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
    if result.returncode != 0:
        print("Fehler beim Abrufen der Tabs:", result.stderr)
        return []
    
    output = result.stdout.strip()
    tabs = []
    for item in output.split("||||"):
        if "|||" in item:
            url, title = item.split("|||", 1)
            tabs.append({"url": url.strip(), "title": title.strip()})
    return tabs

def sanitize_filename(title):
    clean_title = re.sub(r'[/\\?%*:|"<>]', '-', title)
    return clean_title[:150]

def extract_meta_content(html, name_or_prop):
    pattern1 = rf'<meta\s+(?:name|property)=[\'"]{name_or_prop}[\'"]\s+content=[\'"]([^\'"]+)[\'"]'
    pattern2 = rf'<meta\s+content=[\'"]([^\'"]+)[\'"]\s+(?:name|property)=[\'"]{name_or_prop}[\'"]'
    
    match = re.search(pattern1, html, re.IGNORECASE)
    if match: return match.group(1)
    match = re.search(pattern2, html, re.IGNORECASE)
    if match: return match.group(1)
    return ""

def generate_metadata_for_url(url):
    meta = {
        "author": "Unbekannt",
        "description": "Keine Zusammenfassung gefunden.",
        "keywords": "Unbekannt",
        "image": "",
        "word_count": 0
    }
    
    if not url.startswith("http"):
        return meta
        
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'})
        with urllib.request.urlopen(req, timeout=5) as response:
            try:
                html_content = response.read().decode('utf-8', errors='ignore')
            except Exception:
                html_content = ""
            
            author = extract_meta_content(html_content, "author") or extract_meta_content(html_content, "article:author")
            if author: meta["author"] = author
            
            desc = extract_meta_content(html_content, "description") or extract_meta_content(html_content, "og:description")
            if desc: meta["description"] = desc
            
            img = extract_meta_content(html_content, "og:image") or extract_meta_content(html_content, "twitter:image")
            if img: meta["image"] = img
            
            keys = extract_meta_content(html_content, "keywords")
            if keys: meta["keywords"] = keys
            
            text_only = re.sub(r'<[^>]+>', ' ', html_content)
            meta["word_count"] = len(text_only.split())
            
    except Exception:
        pass
        
    return meta

def create_html_database(entries):
    # Sortiere neueste zuerst (wir nehmen an, die Reihenfolge im Array ist chronologisch, also umkehren)
    sorted_entries = list(reversed(entries))
    
    html = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chrome PDF Export - Dokumentenübersicht</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; background-color: #f9f9fb; color: #333; }
        h1 { color: #2c3e50; }
        .stats { background: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: inline-block; }
        table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-radius: 8px; overflow: hidden; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #eee; vertical-align: top; }
        th { background-color: #f1f4f8; font-weight: 600; color: #555; }
        tr:hover { background-color: #fcfcfc; }
        .thumbnail { width: 100px; height: auto; border-radius: 4px; object-fit: cover; }
        .no-image { width: 100px; height: 75px; background: #eee; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #999; border-radius: 4px; text-align: center; padding: 5px; box-sizing: border-box; }
        a { color: #3498db; text-decoration: none; word-break: break-all; }
        a:hover { text-decoration: underline; }
        .meta-text { font-size: 0.9em; line-height: 1.5; color: #555; }
        .badge { display: inline-block; padding: 3px 8px; background: #e8f4f8; color: #2980b9; border-radius: 12px; font-size: 0.8em; margin-right: 4px; margin-bottom: 4px; }
        .fallback-badge { background: #fdf2e9; color: #d35400; }
    </style>
</head>
<body>
    <h1>📚 Deine Dokumentenübersicht</h1>
    <div class="stats">
        <strong>Status:</strong> """ + str(len(entries)) + """ Dokumente erfasst<br>
        <span style="font-size: 0.85em; color: #777;">Zuletzt aktualisiert: """ + datetime.now().strftime("%d.%m.%Y %H:%M") + """</span>
    </div>
    <table>
        <thead>
            <tr>
                <th width="120">Bild</th>
                <th width="20%">Dokument & Links</th>
                <th width="15%">Autor & Quelle</th>
                <th width="20%">Thema / Sparte</th>
                <th width="33%">Hauptthese / Zusammenfassung</th>
            </tr>
        </thead>
        <tbody>
"""
    for entry in sorted_entries:
        title = entry["title"]
        url = entry.get("url", "")
        pdf_file = entry["pdf_filename"]
        meta = entry.get("meta", {})
        
        is_fallback = entry.get("is_fallback", False)
        
        img_html = f'<img src="{meta.get("image", "")}" class="thumbnail" alt="Vorschaubild">' if meta.get("image") else '<div class="no-image">Kein Bild</div>'
        
        keywords_html = ""
        kw_list = meta.get("keywords", "Unbekannt")
        if kw_list and kw_list != "Unbekannt":
            for kw in kw_list.split(','):
                keywords_html += f'<span class="badge">{kw.strip()}</span>'
        else:
            if is_fallback:
                keywords_html = "<span class='badge fallback-badge'>Manuell hinzugefügt</span>"
            else:
                keywords_html = "<span class='meta-text'><em>Nicht angegeben</em></span>"
            
        url_html = f'🌐 <a href="{url}" target="_blank" style="font-size: 0.8em;">Original Webseite</a>' if url else '<span style="font-size: 0.8em; color: #999;">Keine Web-URL vorhanden</span>'
        word_count = meta.get("word_count", 0)
        word_html = f'<span class="meta-text"><strong>Länge:</strong> ~{word_count} Worte</span>' if word_count > 0 else ''
        
        # Check if file exists to visually indicate missing files
        file_exists = os.path.exists(os.path.join(DOWNLOAD_DIR, pdf_file))
        pdf_link = f'📎 <a href="{pdf_file}" target="_blank">Lokal als PDF öffnen</a>' if file_exists else f'<span style="color: #e74c3c;">⚠️ PDF-Datei nicht mehr im Ordner</span>'
        
        html += f"""
            <tr>
                <td>{img_html}</td>
                <td>
                    <strong>{title}</strong><br><br>
                    {pdf_link}<br><br>
                    {url_html}
                </td>
                <td>
                    <strong>Autor:</strong><br>{meta.get("author", "Unbekannt")}<br><br>
                    {word_html}
                </td>
                <td>{keywords_html}</td>
                <td class="meta-text">{meta.get("description", "Keine Zusammenfassung vorhanden.")}</td>
            </tr>
"""
    
    html += """
        </tbody>
    </table>
</body>
</html>
"""
    return html

def main():
    print("Lade bisherige Datenbank...")
    db_entries = load_database()
    
    # Erfasse alle bereits vorhandenen PDFs im Ordner
    existing_pdfs = [f for f in os.listdir(DOWNLOAD_DIR) if f.lower().endswith('.pdf')]
    known_pdfs = {entry["pdf_filename"] for entry in db_entries}
    
    # Füge manuell abgelegte oder alte PDFs zur Datenbank hinzu (als Fallback)
    added_orphans = 0
    for pdf in existing_pdfs:
        if pdf not in known_pdfs:
            db_entries.append({
                "title": pdf.replace('.pdf', '').replace('_', ' '),
                "url": "",
                "pdf_filename": pdf,
                "is_fallback": True,
                "meta": {
                    "author": "Unbekannt",
                    "description": "Dieses PDF wurde manuell in den Ordner gelegt oder früher exportiert, daher gibt es keine Web-Metadaten.",
                    "keywords": "Unbekannt",
                    "image": "",
                    "word_count": 0
                }
            })
            known_pdfs.add(pdf)
            added_orphans += 1
            
    if added_orphans > 0:
        print(f"{added_orphans} neue PDFs im Ordner gefunden und der Datenbank hinzugefügt.")

    print("Rufe aktuell geöffnete Tabs aus Google Chrome ab...")
    tabs = get_chrome_tabs()
    
    if tabs:
        print(f"{len(tabs)} Tabs gefunden. Starte PDF-Export nach {DOWNLOAD_DIR}...")
        
        for i, tab in enumerate(tabs, 1):
            url = tab["url"]
            title = tab["title"]
            
            if not title:
                title = urllib.parse.urlparse(url).netloc
                if not title:
                    title = f"Unbekannter_Tab_{i}"
                    
            filename = sanitize_filename(title) + ".pdf"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            
            counter = 1
            base_filename = filename
            while os.path.exists(filepath):
                filename = f"{base_filename[:-4]}_{counter}.pdf"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                counter += 1
                
            print(f"[{i}/{len(tabs)}] Exportiere: {title}")
            print("  -> Lese Meta-Daten...")
            meta_data = generate_metadata_for_url(url)
            
            db_entries.append({
                "title": title,
                "url": url,
                "pdf_filename": filename,
                "is_fallback": False,
                "meta": meta_data
            })
            
            cmd = [CHROME_PATH, "--headless", "--disable-gpu", f"--print-to-pdf={filepath}", url]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
            except subprocess.TimeoutExpired:
                print(f"  -> Timeout beim PDF-Export")
            except Exception as e:
                print(f"  -> Fehler beim PDF-Export: {e}")
    else:
        print("Keine offenen Tabs gefunden oder Chrome läuft nicht.")

    print("\nSpeichere Datenbank und erstelle HTML-Übersicht...")
    save_database(db_entries)
    
    html_content = create_html_database(db_entries)
    html_path = os.path.join(DOWNLOAD_DIR, "uebersicht.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Fertig! Die HTML-Datenbank findest du unter: {html_path}")

if __name__ == "__main__":
    main()
