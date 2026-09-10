"""DB-Schicht: Schema anlegen, idempotent, Invarianten der Tabellen."""
import sqlite3

import pytest

from bestand.db import verbinde


def test_verbinde_legt_alle_tabellen_an(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")

    tabellen = {z["name"] for z in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"teile", "faecher", "alternativen", "preis_cache"} <= tabellen


def test_verbinde_ist_idempotent_und_erhaelt_daten(tmp_path):
    pfad = tmp_path / "bestand.db"
    conn = verbinde(pfad)
    conn.execute("INSERT INTO faecher (regal, position) VALUES ('A', '3')")
    conn.commit()
    conn.close()

    conn2 = verbinde(pfad)
    zeile = conn2.execute("SELECT regal, position FROM faecher").fetchone()
    assert (zeile["regal"], zeile["position"]) == ("A", "3")


def test_menge_darf_nicht_negativ_werden(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO teile (bezeichnung, menge, angelegt_am)"
                     " VALUES ('X', -1, '2026-09-08')")


def test_fach_ist_je_regal_und_position_eindeutig(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")
    conn.execute("INSERT INTO faecher (regal, position) VALUES ('A', '3')")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO faecher (regal, position) VALUES ('A', '3')")


def test_verbinde_aktiviert_wal(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")

    modus = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert modus == "wal"


def test_fremdschluessel_werden_erzwungen(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO alternativen (teil_id, bezeichnung, datum)"
                     " VALUES (999, 'X', '2026-09-08')")


def test_verbinde_legt_projekt_tabellen_an(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")

    tabellen = {z["name"] for z in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"projekte", "projekt_positionen", "verbrauch"} <= tabellen


def test_referenz_ist_je_projekt_eindeutig(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")
    conn.execute("INSERT INTO projekte (name, angelegt_am) VALUES ('P', '2026-09-10')")
    conn.execute("INSERT INTO projekt_positionen (projekt_id, referenz, bezeichnung)"
                 " VALUES (1, 'C3', 'X')")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO projekt_positionen (projekt_id, referenz, bezeichnung)"
                     " VALUES (1, 'C3', 'Y')")


def test_positions_menge_muss_positiv_sein(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")
    conn.execute("INSERT INTO projekte (name, angelegt_am) VALUES ('P', '2026-09-10')")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO projekt_positionen (projekt_id, referenz,"
                     " bezeichnung, menge) VALUES (1, 'C3', 'X', 0)")


def test_projekt_status_nur_offen_oder_gebaut(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO projekte (name, status, angelegt_am)"
                     " VALUES ('P', 'kaputt', '2026-09-10')")
