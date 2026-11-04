#!/usr/bin/env python3
"""HermesTime: privacy-friendly foreground-app time tracker for macOS.

The tracker is intentionally small and dependency-free. It samples the current
foreground app/window periodically, stores samples in SQLite, and builds daily or
weekly reports from the gaps between samples.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import plistlib
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.parse
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

APP_NAME = "HermesTime"
APP_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
DB_PATH = APP_DIR / "activity.sqlite"
CONFIG_PATH = APP_DIR / "config.json"
DASHBOARD_PATH = APP_DIR / "dashboard.html"
LAUNCH_AGENT_PATH = Path.home() / "Library" / "LaunchAgents" / "com.hermes.time-tracker.plist"

DEFAULT_CONFIG: dict[str, Any] = {
    "sample_interval_seconds": 60,
    "max_gap_seconds": 180,
    "idle_after_seconds": 300,
    "store_window_titles": True,
    # One of: full, domain, off. Domain is a safer default than full URLs.
    "browser_url_scope": "domain",
    "categories": [
        {
            "name": "Entwicklung",
            "apps": ["Visual Studio Code", "Code", "Xcode", "Terminal", "iTerm2", "Warp", "GitHub Desktop"],
            "domains": ["github.com", "stackoverflow.com", "docs.python.org", "developer.apple.com"],
            "title_keywords": ["python", "javascript", "typescript", "git", "pull request", "issue"],
        },
        {
            "name": "Kommunikation",
            "apps": ["Mail", "Microsoft Outlook", "Messages", "Signal", "Telegram", "Slack", "Microsoft Teams", "Zoom"],
            "domains": ["mail.google.com", "outlook.office.com", "teams.microsoft.com", "slack.com"],
            "title_keywords": ["posteingang", "inbox", "meeting", "calendar", "kalender"],
        },
        {
            "name": "Recherche / Lesen",
            "apps": ["Books", "Preview", "Skim", "Zotero"],
            "domains": ["pubmed.ncbi.nlm.nih.gov", "scholar.google.com", "arxiv.org", "wikipedia.org", "ncbi.nlm.nih.gov"],
            "title_keywords": ["pubmed", "abstract", "paper", "studie", "leitlinie", "guideline"],
        },
        {
            "name": "Organisation / Dateien",
            "apps": ["Finder", "Calendar", "Reminders", "Notes", "Obsidian", "Notion"],
            "domains": ["calendar.google.com", "notion.so"],
            "title_keywords": ["todo", "aufgabe", "planung", "plan"],
        },
        {
            "name": "Ablenkung / Medien",
            "apps": ["Music", "TV", "Spotify", "Steam"],
            "domains": ["youtube.com", "netflix.com", "instagram.com", "facebook.com", "reddit.com", "x.com", "twitter.com"],
            "title_keywords": ["youtube", "netflix", "reddit", "instagram"],
        },
    ],
}

BROWSER_APPS = {
    "Safari": "safari",
    "Google Chrome": "chromium",
    "Chrome": "chromium",
    "Chromium": "chromium",
    "Arc": "chromium",
    "Microsoft Edge": "chromium",
    "Brave Browser": "chromium",
    "Vivaldi": "chromium",
}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    app_name TEXT NOT NULL,
    window_title TEXT,
    url TEXT,
    domain TEXT,
    category TEXT NOT NULL,
    idle_seconds REAL NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'sampler'
);
CREATE INDEX IF NOT EXISTS idx_samples_ts ON samples(ts);
CREATE INDEX IF NOT EXISTS idx_samples_category ON samples(category);
"""


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_ts(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def fmt_duration(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s" if seconds < 600 else f"{minutes}m"
    return f"{secs}s"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(base))
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def ensure_app_dir() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    ensure_app_dir()
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        user_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Config ist kein gültiges JSON: {CONFIG_PATH}: {exc}") from exc
    return deep_merge(DEFAULT_CONFIG, user_config)


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    ensure_app_dir()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    return conn


def run_command(args: list[str], timeout: int = 5) -> str | None:
    try:
        result = subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout)
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def run_osascript(script: str, timeout: int = 5) -> str | None:
    return run_command(["osascript", "-e", script], timeout=timeout)


def get_idle_seconds() -> float:
    output = run_command(["ioreg", "-c", "IOHIDSystem"], timeout=5)
    if not output:
        return 0.0
    match = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', output)
    if not match:
        return 0.0
    return int(match.group(1)) / 1_000_000_000


def get_frontmost_app_and_title() -> tuple[str, str]:
    script = r'''
    set delimiter to "|HERMES_TIME|"
    tell application "System Events"
      set frontProc to first application process whose frontmost is true
      set appName to name of frontProc
      set winTitle to ""
      try
        if (count of windows of frontProc) > 0 then set winTitle to name of front window of frontProc
      end try
    end tell
    return appName & delimiter & winTitle
    '''
    output = run_osascript(script)
    if not output or "|HERMES_TIME|" not in output:
        return "Unbekannt", ""
    app_name, window_title = output.split("|HERMES_TIME|", 1)
    return app_name.strip() or "Unbekannt", window_title.strip()


def get_browser_url(app_name: str) -> str | None:
    browser_kind = BROWSER_APPS.get(app_name)
    if browser_kind == "safari":
        script = 'tell application "Safari" to if (count of documents) > 0 then return URL of front document'
    elif browser_kind == "chromium":
        escaped_app = app_name.replace('"', '\\"')
        script = f'tell application "{escaped_app}" to if (count of windows) > 0 then return URL of active tab of front window'
    else:
        return None
    url = run_osascript(script)
    if not url or not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        return None
    return url.strip()


def domain_from_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urllib.parse.urlparse(url)
    domain = (parsed.hostname or "").lower().removeprefix("www.")
    return domain or None


def apply_url_scope(url: str | None, domain: str | None, scope: str) -> str | None:
    if not url or scope == "off":
        return None
    if scope == "domain":
        return f"https://{domain}" if domain else None
    return url


def classify(app_name: str, window_title: str, domain: str | None, idle_seconds: float, config: dict[str, Any]) -> str:
    if idle_seconds >= float(config.get("idle_after_seconds", 300)):
        return "Pause / Idle"

    app_l = app_name.lower()
    title_l = window_title.lower()
    domain_l = (domain or "").lower()

    for rule in config.get("categories", []):
        apps = [str(a).lower() for a in rule.get("apps", [])]
        domains = [str(d).lower().removeprefix("www.") for d in rule.get("domains", [])]
        keywords = [str(k).lower() for k in rule.get("title_keywords", [])]
        if any(app_l == app or app_l.endswith(app) or app in app_l for app in apps):
            return str(rule.get("name", "Unklassifiziert"))
        if domain_l and any(domain_l == d or domain_l.endswith("." + d) for d in domains):
            return str(rule.get("name", "Unklassifiziert"))
        if any(keyword in title_l for keyword in keywords):
            return str(rule.get("name", "Unklassifiziert"))

    if app_name in BROWSER_APPS:
        return "Browser / Unklassifiziert"
    return "Unklassifiziert"


def sample_activity(config: dict[str, Any]) -> dict[str, Any]:
    app_name, window_title = get_frontmost_app_and_title()
    if not bool(config.get("store_window_titles", True)):
        window_title = ""
    raw_url = get_browser_url(app_name)
    domain = domain_from_url(raw_url)
    stored_url = apply_url_scope(raw_url, domain, str(config.get("browser_url_scope", "domain")))
    idle_seconds = get_idle_seconds()
    category = classify(app_name, window_title, domain, idle_seconds, config)
    return {
        "ts": now_utc().isoformat(timespec="seconds"),
        "app_name": app_name,
        "window_title": window_title,
        "url": stored_url,
        "domain": domain,
        "category": category,
        "idle_seconds": idle_seconds,
        "source": "sampler",
    }


def insert_sample(conn: sqlite3.Connection, sample: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO samples (ts, app_name, window_title, url, domain, category, idle_seconds, source)
        VALUES (:ts, :app_name, :window_title, :url, :domain, :category, :idle_seconds, :source)
        """,
        sample,
    )
    conn.commit()


def record_once(config: dict[str, Any], db_path: Path = DB_PATH) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        sample = sample_activity(config)
        insert_sample(conn, sample)
        return sample
    finally:
        conn.close()


def run_daemon(config: dict[str, Any], db_path: Path = DB_PATH) -> None:
    interval = max(10, int(config.get("sample_interval_seconds", 60)))
    print(f"HermesTime läuft. Schreibe nach {db_path}. Intervall: {interval}s. Abbruch: Ctrl+C")
    while True:
        sample = record_once(config, db_path)
        print(f"{sample['ts']}  {sample['category']}  {sample['app_name']}  {sample.get('domain') or ''}", flush=True)
        time.sleep(interval)


def period_start(period: str, date_text: str | None) -> dt.datetime:
    local_today = dt.date.fromisoformat(date_text) if date_text else dt.date.today()
    if period == "day":
        start_date = local_today
    elif period == "week":
        start_date = local_today - dt.timedelta(days=local_today.weekday())
    else:
        raise ValueError(f"Unbekannte Periode: {period}")
    local_start = dt.datetime.combine(start_date, dt.time.min).astimezone()
    return local_start.astimezone(dt.timezone.utc)


def fetch_samples(conn: sqlite3.Connection, start: dt.datetime, end: dt.datetime) -> list[sqlite3.Row]:
    cursor = conn.execute(
        """
        SELECT * FROM samples
        WHERE ts >= ? AND ts <= ?
        ORDER BY ts ASC, id ASC
        """,
        (start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")),
    )
    return list(cursor.fetchall())


def build_report_data(
    conn: sqlite3.Connection,
    period: str = "day",
    date_text: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or load_config()
    start = period_start(period, date_text)
    end = now_utc()
    if period == "week":
        end = min(end, start + dt.timedelta(days=7))
    elif period == "day":
        end = min(end, start + dt.timedelta(days=1))

    samples = fetch_samples(conn, start, end)
    max_gap = float(config.get("max_gap_seconds", 180))
    default_last_gap = min(float(config.get("sample_interval_seconds", 60)), max_gap)

    category_seconds: defaultdict[str, float] = defaultdict(float)
    app_seconds: defaultdict[str, float] = defaultdict(float)
    domain_seconds: defaultdict[str, float] = defaultdict(float)
    focus_blocks: list[dict[str, Any]] = []

    previous_block: dict[str, Any] | None = None
    for index, sample in enumerate(samples):
        ts = parse_ts(sample["ts"])
        if index + 1 < len(samples):
            next_ts = parse_ts(samples[index + 1]["ts"])
            duration = min(max_gap, max(0.0, (next_ts - ts).total_seconds()))
        else:
            duration = min(default_last_gap, max(0.0, (end - ts).total_seconds()))
        if duration <= 0:
            continue

        category = sample["category"] or "Unklassifiziert"
        app_name = sample["app_name"] or "Unbekannt"
        domain = sample["domain"] or ""
        category_seconds[category] += duration
        app_seconds[app_name] += duration
        if domain:
            domain_seconds[domain] += duration

        # Merge consecutive samples with same category/app/domain into focus blocks.
        block_key = (category, app_name, domain)
        if previous_block and previous_block["key"] == block_key and (ts - previous_block["end"]).total_seconds() <= max_gap:
            previous_block["end"] = ts + dt.timedelta(seconds=duration)
            previous_block["seconds"] += duration
        else:
            previous_block = {
                "key": block_key,
                "start": ts,
                "end": ts + dt.timedelta(seconds=duration),
                "seconds": duration,
                "category": category,
                "app_name": app_name,
                "domain": domain,
                "title": sample["window_title"] or "",
            }
            focus_blocks.append(previous_block)

    focus_blocks = [block for block in focus_blocks if block["seconds"] >= 10 * 60]
    focus_blocks.sort(key=lambda b: b["seconds"], reverse=True)

    return {
        "period": period,
        "start": start,
        "end": end,
        "sample_count": len(samples),
        "category_seconds": dict(sorted(category_seconds.items(), key=lambda item: item[1], reverse=True)),
        "app_seconds": dict(sorted(app_seconds.items(), key=lambda item: item[1], reverse=True)),
        "domain_seconds": dict(sorted(domain_seconds.items(), key=lambda item: item[1], reverse=True)),
        "focus_blocks": focus_blocks[:8],
    }


def local_time_text(value: dt.datetime) -> str:
    return value.astimezone().strftime("%H:%M")


def render_text_report(data: dict[str, Any]) -> str:
    active_total = sum(seconds for category, seconds in data["category_seconds"].items() if category != "Pause / Idle")
    idle_total = data["category_seconds"].get("Pause / Idle", 0)
    date_label = data["start"].astimezone().strftime("%d.%m.%Y")
    title = "Tagesbericht" if data["period"] == "day" else "Wochenbericht"
    lines = [
        f"{title} – {date_label}",
        "",
        f"Aktive Zeit: {fmt_duration(active_total)}",
    ]
    if idle_total:
        lines.append(f"Pausen/Idle: {fmt_duration(idle_total)}")
    lines.extend([f"Samples: {data['sample_count']}", "", "Nach Kategorien:"])
    for category, seconds in data["category_seconds"].items():
        lines.append(f"  {category:<26} {fmt_duration(seconds)}")

    lines.extend(["", "Top-Apps:"])
    for app_name, seconds in list(data["app_seconds"].items())[:10]:
        lines.append(f"  {app_name:<26} {fmt_duration(seconds)}")

    if data["domain_seconds"]:
        lines.extend(["", "Top-Domains:"])
        for domain, seconds in list(data["domain_seconds"].items())[:10]:
            lines.append(f"  {domain:<26} {fmt_duration(seconds)}")

    if data["focus_blocks"]:
        lines.extend(["", "Längere Blöcke:"])
        for block in data["focus_blocks"]:
            target = block["domain"] or block["app_name"]
            lines.append(
                f"  {local_time_text(block['start'])}–{local_time_text(block['end'])} "
                f"{block['category']} · {target} · {fmt_duration(block['seconds'])}"
            )
    return "\n".join(lines)


def render_html_report(data: dict[str, Any]) -> str:
    category_rows = "".join(
        f"<tr><td>{html.escape(category)}</td><td>{fmt_duration(seconds)}</td></tr>"
        for category, seconds in data["category_seconds"].items()
    )
    app_rows = "".join(
        f"<tr><td>{html.escape(app)}</td><td>{fmt_duration(seconds)}</td></tr>"
        for app, seconds in list(data["app_seconds"].items())[:12]
    )
    domain_rows = "".join(
        f"<tr><td>{html.escape(domain)}</td><td>{fmt_duration(seconds)}</td></tr>"
        for domain, seconds in list(data["domain_seconds"].items())[:12]
    )
    block_rows = "".join(
        f"<li><strong>{local_time_text(block['start'])}–{local_time_text(block['end'])}</strong> "
        f"{html.escape(block['category'])} · {html.escape(block['domain'] or block['app_name'])} "
        f"<span>{fmt_duration(block['seconds'])}</span></li>"
        for block in data["focus_blocks"]
    )
    active_total = sum(seconds for category, seconds in data["category_seconds"].items() if category != "Pause / Idle")
    generated = dt.datetime.now().astimezone().strftime("%d.%m.%Y %H:%M")
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HermesTime Dashboard</title>
  <style>
    :root {{ color-scheme: light dark; --accent: #5db83a; --bg: #f6faf4; --card: #ffffff; --text: #243024; }}
    @media (prefers-color-scheme: dark) {{ :root {{ --bg: #111711; --card: #1b241b; --text: #e8f1e5; }} }}
    body {{ margin: 0; font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }}
    main {{ max-width: 980px; margin: 0 auto; padding: 32px 18px; }}
    h1 {{ margin: 0 0 6px; font-size: 32px; }}
    .muted {{ color: color-mix(in srgb, var(--text) 62%, transparent); }}
    .hero {{ background: linear-gradient(135deg, rgba(93,184,58,.22), rgba(126,200,80,.06)); border: 1px solid rgba(93,184,58,.25); border-radius: 24px; padding: 24px; margin-bottom: 18px; }}
    .metric {{ font-size: 42px; font-weight: 750; letter-spacing: -0.04em; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }}
    section {{ background: var(--card); border-radius: 20px; padding: 18px; box-shadow: 0 8px 30px rgba(0,0,0,.06); }}
    table {{ width: 100%; border-collapse: collapse; }}
    td {{ padding: 8px 0; border-bottom: 1px solid rgba(127,127,127,.18); }}
    td:last-child {{ text-align: right; font-variant-numeric: tabular-nums; }}
    ul {{ padding-left: 20px; }}
    li {{ margin: 10px 0; }}
    li span {{ color: var(--accent); font-weight: 700; }}
  </style>
</head>
<body>
<main>
  <div class="hero">
    <h1>HermesTime</h1>
    <div class="muted">Generiert am {html.escape(generated)} · Samples: {data['sample_count']}</div>
    <div class="metric">{fmt_duration(active_total)}</div>
    <div>aktive Zeit im ausgewählten Zeitraum</div>
  </div>
  <div class="grid">
    <section><h2>Kategorien</h2><table>{category_rows or '<tr><td>Keine Daten</td><td>–</td></tr>'}</table></section>
    <section><h2>Apps</h2><table>{app_rows or '<tr><td>Keine Daten</td><td>–</td></tr>'}</table></section>
    <section><h2>Domains</h2><table>{domain_rows or '<tr><td>Keine Daten</td><td>–</td></tr>'}</table></section>
    <section><h2>Längere Blöcke</h2><ul>{block_rows or '<li>Noch keine Blöcke ≥ 10 Minuten.</li>'}</ul></section>
  </div>
</main>
</body>
</html>
"""


def write_dashboard(period: str, date_text: str | None, output: Path, config: dict[str, Any]) -> Path:
    conn = connect()
    try:
        data = build_report_data(conn, period=period, date_text=date_text, config=config)
    finally:
        conn.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html_report(data), encoding="utf-8")
    return output


def install_launch_agent(script_path: Path, config: dict[str, Any]) -> Path:
    interval = max(10, int(config.get("sample_interval_seconds", 60)))
    plist = {
        "Label": "com.hermes.time-tracker",
        "ProgramArguments": [sys.executable, str(script_path.resolve()), "record"],
        "StartInterval": interval,
        "RunAtLoad": True,
        "StandardOutPath": str(APP_DIR / "launchd.log"),
        "StandardErrorPath": str(APP_DIR / "launchd.err.log"),
    }
    ensure_app_dir()
    LAUNCH_AGENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LAUNCH_AGENT_PATH.open("wb") as file:
        plistlib.dump(plist, file)
    subprocess.run(["launchctl", "unload", str(LAUNCH_AGENT_PATH)], check=False, capture_output=True)
    result = subprocess.run(["launchctl", "load", str(LAUNCH_AGENT_PATH)], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"launchctl load fehlgeschlagen: {result.stderr.strip()}")
    return LAUNCH_AGENT_PATH


def uninstall_launch_agent() -> None:
    if LAUNCH_AGENT_PATH.exists():
        subprocess.run(["launchctl", "unload", str(LAUNCH_AGENT_PATH)], check=False, capture_output=True)
        LAUNCH_AGENT_PATH.unlink()


def seed_test_data(conn: sqlite3.Connection, config: dict[str, Any]) -> None:
    base = now_utc() - dt.timedelta(hours=2)
    rows = [
        (0, "Code", "mac_time_tracker.py", None, None),
        (60, "Code", "mac_time_tracker.py", None, None),
        (120, "Safari", "PubMed Studie", "https://pubmed.ncbi.nlm.nih.gov/123/", "pubmed.ncbi.nlm.nih.gov"),
        (180, "Safari", "PubMed Studie", "https://pubmed.ncbi.nlm.nih.gov/123/", "pubmed.ncbi.nlm.nih.gov"),
        (240, "Microsoft Outlook", "Inbox", None, None),
    ]
    for seconds, app, title, url, domain in rows:
        idle = 0.0
        sample = {
            "ts": (base + dt.timedelta(seconds=seconds)).isoformat(timespec="seconds"),
            "app_name": app,
            "window_title": title,
            "url": url,
            "domain": domain,
            "category": classify(app, title, domain, idle, config),
            "idle_seconds": idle,
            "source": "selftest",
        }
        insert_sample(conn, sample)


def selftest() -> None:
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.sqlite"
        conn = connect(db_path)
        try:
            seed_test_data(conn, config)
            data = build_report_data(conn, period="day", config=config)
            report = render_text_report(data)
            if "Entwicklung" not in report or "Recherche / Lesen" not in report or data["sample_count"] != 5:
                raise AssertionError(report)
            html_report = render_html_report(data)
            if "HermesTime" not in html_report or "Kategorien" not in html_report:
                raise AssertionError("HTML report missing expected markers")
        finally:
            conn.close()
    print("Selftest OK")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lokaler macOS-Zeittracker mit SQLite und HTML-Report.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Config und Datenbank anlegen")
    sub.add_parser("record", help="Ein Sample erfassen")
    sub.add_parser("daemon", help="Im Vordergrund dauerhaft samplen")

    report_parser = sub.add_parser("report", help="Textbericht ausgeben")
    report_parser.add_argument("--period", choices=["day", "week"], default="day")
    report_parser.add_argument("--date", help="Datum im Format YYYY-MM-DD; Default: heute")

    dashboard_parser = sub.add_parser("dashboard", help="HTML-Dashboard erzeugen")
    dashboard_parser.add_argument("--period", choices=["day", "week"], default="day")
    dashboard_parser.add_argument("--date", help="Datum im Format YYYY-MM-DD; Default: heute")
    dashboard_parser.add_argument("--output", type=Path, default=DASHBOARD_PATH)
    dashboard_parser.add_argument("--open", action="store_true", help="Dashboard nach dem Erzeugen öffnen")

    sub.add_parser("install-launch-agent", help="launchd-Job installieren, der regelmäßig record ausführt")
    sub.add_parser("uninstall-launch-agent", help="launchd-Job entfernen")
    sub.add_parser("selftest", help="Interne Logik ohne macOS-Rechte testen")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "selftest":
        selftest()
        return 0

    config = load_config()

    if args.command == "init":
        conn = connect()
        conn.close()
        print(f"Config: {CONFIG_PATH}")
        print(f"Datenbank: {DB_PATH}")
        return 0

    if args.command == "record":
        sample = record_once(config)
        print(json.dumps(sample, ensure_ascii=False, indent=2))
        return 0

    if args.command == "daemon":
        run_daemon(config)
        return 0

    if args.command == "report":
        conn = connect()
        try:
            data = build_report_data(conn, period=args.period, date_text=args.date, config=config)
        finally:
            conn.close()
        print(render_text_report(data))
        return 0

    if args.command == "dashboard":
        output = write_dashboard(args.period, args.date, args.output, config)
        print(output)
        if args.open:
            subprocess.run(["open", str(output)], check=False)
        return 0

    if args.command == "install-launch-agent":
        plist_path = install_launch_agent(Path(__file__), config)
        print(f"Installiert: {plist_path}")
        print("Falls keine App-/Fenstertitel erfasst werden: Systemeinstellungen → Datenschutz & Sicherheit → Bedienungshilfen → Terminal/Hermes erlauben.")
        return 0

    if args.command == "uninstall-launch-agent":
        uninstall_launch_agent()
        print("LaunchAgent entfernt.")
        return 0

    parser.error(f"Unbekannter Befehl: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
