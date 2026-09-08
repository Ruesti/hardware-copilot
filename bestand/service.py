"""Geschäftslogik des Bestands (Spec §3.2): ein Dienst, eine DB-Datei.

Fehler sind BestandsFehler mit nutzertauglicher Meldung; der MCP-Layer reicht
sie als ⚠-Zeile durch. Datum ist injizierbar (Tests), Default = heute.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from . import db
from . import format as fmt


class BestandsFehler(Exception):
    """Fachlicher Fehler — die Meldung ist für den Nutzer bestimmt."""


class BestandsDienst:
    def __init__(self, db_pfad: Path | str, regal_url: str | None = None,
                 heute=None, sender=None):
        self._conn = db.verbinde(db_pfad)
        self._regal_url = regal_url
        self._heute = heute or (lambda: date.today().isoformat())
        self._sender = sender  # ab Task 5: bestand.regal.sende

    # -- intern ---------------------------------------------------------------

    def _fach_id(self, fach: str) -> int:
        if "/" not in fach:
            raise BestandsFehler(
                f'Fach „{fach}" nicht verstanden — Format ist Regal/Position, z. B. A/3.')
        regal, position = fach.split("/", 1)
        self._conn.execute(
            "INSERT OR IGNORE INTO faecher (regal, position) VALUES (?, ?)",
            (regal, position))
        zeile = self._conn.execute(
            "SELECT id FROM faecher WHERE regal = ? AND position = ?",
            (regal, position)).fetchone()
        return zeile["id"]

    def _teil(self, teil_id: int) -> dict:
        zeile = self._conn.execute(
            "SELECT t.*, f.regal, f.position FROM teile t"
            " LEFT JOIN faecher f ON f.id = t.fach_id WHERE t.id = ?",
            (teil_id,)).fetchone()
        if zeile is None:
            raise BestandsFehler(f"Kein Teil mit ID T-{teil_id}.")
        d = dict(zeile)
        d["fach"] = f"{d['regal']}/{d['position']}" if d["regal"] else None
        return d

    # -- Werkzeuge ------------------------------------------------------------

    def anlegen(self, bezeichnung: str, menge: int, fach: str, klasse: str = "",
                hersteller_nr: str = "", eckdaten: str = "",
                datenblatt_url: str = "") -> str:
        fach_id = self._fach_id(fach)
        cur = self._conn.execute(
            "INSERT INTO teile (bezeichnung, hersteller_nr, klasse, menge,"
            " eckdaten, datenblatt_url, fach_id, angelegt_am)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (bezeichnung, hersteller_nr, klasse, menge, eckdaten,
             datenblatt_url, fach_id, self._heute()))
        self._conn.commit()
        return (f"[T-{cur.lastrowid}] {bezeichnung} angelegt — "
                f"Menge {menge}, Fach {fach}.")

    def suchen(self, suchbegriff: str, klasse: str | None = None) -> str:
        m = re.fullmatch(r"T-(\d+)", suchbegriff.strip())
        if m:
            teil_id = int(m.group(1))
            alternativen = [dict(z) for z in self._conn.execute(
                "SELECT * FROM alternativen WHERE teil_id = ? ORDER BY datum DESC",
                (teil_id,))]
            preise = [dict(z) for z in self._conn.execute(
                "SELECT * FROM preis_cache WHERE teil_id = ? ORDER BY datum DESC",
                (teil_id,))]
            return fmt.detail(self._teil(teil_id), alternativen, preise)

        muster = f"%{suchbegriff}%"
        sql = ("SELECT t.id, t.bezeichnung, t.menge, t.klasse, f.regal, f.position"
               " FROM teile t LEFT JOIN faecher f ON f.id = t.fach_id"
               " WHERE (t.bezeichnung LIKE ? OR t.hersteller_nr LIKE ?"
               "        OR t.eckdaten LIKE ?)")
        parameter: list = [muster, muster, muster]
        if klasse:
            sql += " AND t.klasse = ?"
            parameter.append(klasse)
        zeilen = self._conn.execute(sql + " ORDER BY t.id", parameter).fetchall()
        if not zeilen:
            return (f'Kein Teil gefunden für „{suchbegriff}". '
                    "Neu erfassen: teil_anlegen.")
        return "\n".join(fmt.kurzzeile({
            "id": z["id"], "bezeichnung": z["bezeichnung"], "menge": z["menge"],
            "klasse": z["klasse"],
            "fach": f"{z['regal']}/{z['position']}" if z["regal"] else None,
        }) for z in zeilen)
