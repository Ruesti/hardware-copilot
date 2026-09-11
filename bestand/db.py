"""Bestands-DB: SQLite-Schema anlegen und Verbindung liefern (Spec §3.1, Etappe E1).

Die DB-Datei ist die einzige Wahrheit (Spec §6); der Pfad kommt vom Aufrufer
(MCP-Server: Umgebungsvariable BESTAND_DB). projekte/verbrauch seit E5.
WAL-Modus und busy_timeout, weil ab E2 App-Backend und MCP-Server dieselbe Datei
nebeneinander lesen.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS faecher (
    id INTEGER PRIMARY KEY,
    regal TEXT NOT NULL,
    position TEXT NOT NULL,
    led_nummer INTEGER,
    UNIQUE (regal, position)
);
CREATE TABLE IF NOT EXISTS teile (
    id INTEGER PRIMARY KEY,
    bezeichnung TEXT NOT NULL,
    hersteller_nr TEXT NOT NULL DEFAULT '',
    klasse TEXT NOT NULL DEFAULT '',
    menge INTEGER NOT NULL DEFAULT 0 CHECK (menge >= 0),
    eckdaten TEXT NOT NULL DEFAULT '',
    datenblatt_url TEXT NOT NULL DEFAULT '',
    fach_id INTEGER REFERENCES faecher(id),
    angelegt_am TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alternativen (
    id INTEGER PRIMARY KEY,
    teil_id INTEGER NOT NULL REFERENCES teile(id),
    bezeichnung TEXT NOT NULL,
    hersteller_nr TEXT NOT NULL DEFAULT '',
    hinweis TEXT NOT NULL DEFAULT '',
    datum TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS preis_cache (
    id INTEGER PRIMARY KEY,
    teil_id INTEGER NOT NULL REFERENCES teile(id),
    quelle TEXT NOT NULL,
    preis_eur REAL NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    datum TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projekte (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    beschreibung TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'offen' CHECK (status IN ('offen', 'gebaut')),
    angelegt_am TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projekt_positionen (
    id INTEGER PRIMARY KEY,
    projekt_id INTEGER NOT NULL REFERENCES projekte(id),
    referenz TEXT NOT NULL,
    bezeichnung TEXT NOT NULL,
    menge INTEGER NOT NULL DEFAULT 1 CHECK (menge > 0),
    klasse TEXT NOT NULL DEFAULT '',
    baugruppe TEXT NOT NULL DEFAULT '',
    teil_id INTEGER REFERENCES teile(id),
    pins TEXT,
    kicad_symbol TEXT NOT NULL DEFAULT '',
    kicad_footprint TEXT NOT NULL DEFAULT '',
    notiz TEXT NOT NULL DEFAULT '',
    UNIQUE (projekt_id, referenz)
);
CREATE TABLE IF NOT EXISTS verbrauch (
    id INTEGER PRIMARY KEY,
    projekt_id INTEGER NOT NULL REFERENCES projekte(id),
    teil_id INTEGER NOT NULL REFERENCES teile(id),
    menge INTEGER NOT NULL,
    datum TEXT NOT NULL
);
"""


def verbinde(pfad: Path | str) -> sqlite3.Connection:
    """Öffnet die Bestands-DB und legt fehlende Tabellen an (idempotent)."""
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(pfad)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 3000")
    conn.executescript(_SCHEMA)
    return conn
