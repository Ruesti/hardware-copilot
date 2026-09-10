"""Projekte + Stückliste (Spec E5 §2): anlegen, Positionen, verknüpfen.

Bauart wie service.py: eigene Verbindung, Fehler als BestandsFehler mit
deutscher Meldung, Datum injizierbar (Tests), Commit je Operation.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from . import db
from .service import BestandsFehler


class ProjektDienst:
    def __init__(self, db_pfad: Path | str, heute=None):
        self._conn = db.verbinde(db_pfad)
        self._heute = heute or (lambda: date.today().isoformat())

    # -- intern ---------------------------------------------------------------

    def _projekt(self, projekt_id: int) -> dict:
        zeile = self._conn.execute(
            "SELECT * FROM projekte WHERE id = ?", (projekt_id,)).fetchone()
        if zeile is None:
            raise BestandsFehler(f"Kein Projekt mit ID P-{projekt_id}.")
        return dict(zeile)

    def _teil_existiert(self, teil_id: int) -> None:
        zeile = self._conn.execute(
            "SELECT id FROM teile WHERE id = ?", (teil_id,)).fetchone()
        if zeile is None:
            raise BestandsFehler(f"Kein Teil mit ID T-{teil_id}.")

    def _position(self, projekt_id: int, referenz: str) -> dict:
        zeile = self._conn.execute(
            "SELECT * FROM projekt_positionen WHERE projekt_id = ? AND referenz = ?",
            (projekt_id, referenz)).fetchone()
        if zeile is None:
            raise BestandsFehler(
                f"Keine Position {referenz} in [P-{projekt_id}].")
        return dict(zeile)

    # -- Werkzeuge --------------------------------------------------------------

    def anlegen(self, name: str, beschreibung: str = "") -> str:
        cur = self._conn.execute(
            "INSERT INTO projekte (name, beschreibung, angelegt_am)"
            " VALUES (?, ?, ?)", (name, beschreibung, self._heute()))
        self._conn.commit()
        return f"[P-{cur.lastrowid}] {name} angelegt."

    def position_hinzufuegen(self, projekt_id: int, referenz: str,
                             bezeichnung: str, menge: int = 1, klasse: str = "",
                             teil_id: int | None = None, baugruppe: str = "",
                             pins: dict[str, str] | None = None,
                             kicad_symbol: str = "", kicad_footprint: str = "",
                             notiz: str = "") -> str:
        projekt = self._projekt(projekt_id)
        if projekt["status"] == "gebaut":
            raise BestandsFehler(
                f"[P-{projekt_id}] ist abgeschlossen — keine Änderungen mehr.")
        if menge < 1:
            raise BestandsFehler(f"Menge muss ≥ 1 sein, war {menge}.")
        vorhanden = self._conn.execute(
            "SELECT id FROM projekt_positionen WHERE projekt_id = ? AND referenz = ?",
            (projekt_id, referenz)).fetchone()
        if vorhanden is not None:
            raise BestandsFehler(
                f"Referenz „{referenz}“ existiert schon in [P-{projekt_id}].")
        if teil_id is not None:
            self._teil_existiert(teil_id)
        pins_json = json.dumps(pins) if pins is not None else None
        self._conn.execute(
            "INSERT INTO projekt_positionen (projekt_id, referenz, bezeichnung,"
            " menge, klasse, baugruppe, teil_id, pins, kicad_symbol,"
            " kicad_footprint, notiz) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (projekt_id, referenz, bezeichnung, menge, klasse, baugruppe,
             teil_id, pins_json, kicad_symbol, kicad_footprint, notiz))
        self._conn.commit()
        return f"[P-{projekt_id}] Position {referenz} ({bezeichnung}) hinzugefügt."

    def position_verknuepfen(self, projekt_id: int, referenz: str,
                             teil_id: int) -> str:
        self._projekt(projekt_id)
        self._position(projekt_id, referenz)
        self._teil_existiert(teil_id)
        self._conn.execute(
            "UPDATE projekt_positionen SET teil_id = ?"
            " WHERE projekt_id = ? AND referenz = ?",
            (teil_id, projekt_id, referenz))
        self._conn.commit()
        return f"[P-{projekt_id}] {referenz} → [T-{teil_id}] verknüpft."
