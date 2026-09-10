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

    # -- Abgleich + Daten -------------------------------------------------------

    def _preise_je_teil(self, teil_id: int) -> list[dict]:
        """Je Quelle der neueste Eintrag (höchstes Datum, bei Gleichstand
        höchste ID), Ergebnis aufsteigend nach Preis."""
        zeilen = self._conn.execute(
            "SELECT * FROM preis_cache WHERE teil_id = ?"
            " ORDER BY quelle, datum DESC, id DESC", (teil_id,)).fetchall()
        neueste_je_quelle: dict[str, dict] = {}
        for z in zeilen:
            neueste_je_quelle.setdefault(z["quelle"], dict(z))
        return [{"preis_eur": z["preis_eur"], "quelle": z["quelle"],
                 "datum": z["datum"], "url": z["url"]}
                for z in sorted(neueste_je_quelle.values(),
                                key=lambda z: z["preis_eur"])]

    def projekt_daten(self, projekt_id: int) -> dict:
        projekt = self._projekt(projekt_id)
        zeilen = self._conn.execute(
            "SELECT * FROM projekt_positionen WHERE projekt_id = ? ORDER BY id",
            (projekt_id,)).fetchall()
        positionen = [self._position_daten(z) for z in zeilen]
        return {"id": projekt["id"], "name": projekt["name"],
                "beschreibung": projekt["beschreibung"],
                "status": projekt["status"], "angelegt_am": projekt["angelegt_am"],
                "positionen": positionen,
                "zusammenfassung": self._zusammenfassung(positionen)}

    def _position_daten(self, z) -> dict:
        pos = {"id": z["id"], "referenz": z["referenz"],
               "bezeichnung": z["bezeichnung"], "menge": z["menge"],
               "klasse": z["klasse"], "baugruppe": z["baugruppe"],
               "teil_id": z["teil_id"],
               "pins": json.loads(z["pins"]) if z["pins"] is not None else None,
               "kicad_symbol": z["kicad_symbol"],
               "kicad_footprint": z["kicad_footprint"], "notiz": z["notiz"]}
        teil_id = z["teil_id"]
        if teil_id is None:
            pos["bestand"] = None
            pos["status"] = "nicht_zugeordnet"
            pos["preis"] = None
            pos["alle_preise"] = []
            return pos
        teil = self._conn.execute(
            "SELECT t.menge, f.regal, f.position FROM teile t"
            " LEFT JOIN faecher f ON f.id = t.fach_id WHERE t.id = ?",
            (teil_id,)).fetchone()
        vorrat = teil["menge"]
        fach = f"{teil['regal']}/{teil['position']}" if teil["regal"] else None
        pos["bestand"] = {"menge": vorrat, "fach": fach}
        if vorrat >= pos["menge"]:
            pos["status"] = "da"
        elif vorrat > 0:
            pos["status"] = "knapp"
        else:
            pos["status"] = "fehlt"
        alle_preise = self._preise_je_teil(teil_id)
        pos["alle_preise"] = alle_preise
        pos["preis"] = alle_preise[0] if alle_preise else None
        return pos

    def _zusammenfassung(self, positionen: list[dict]) -> dict:
        gedeckt = sum(1 for p in positionen if p["status"] == "da")
        fehlend = [p for p in positionen if p["status"] != "da"]
        kosten = 0.0
        ohne_preis = 0
        for p in fehlend:
            if p["preis"] is None:
                ohne_preis += 1
                continue
            if p["status"] == "knapp":
                fehlmenge = p["menge"] - p["bestand"]["menge"]
            else:  # fehlt
                fehlmenge = p["menge"]
            kosten += fehlmenge * p["preis"]["preis_eur"]
        return {"positionen": len(positionen), "gedeckt": gedeckt,
                "fehlen": len(fehlend), "fehlteile_kosten_eur": kosten,
                "ohne_preis": ohne_preis}

    def projekte_daten(self) -> list[dict]:
        ids = [z["id"] for z in
               self._conn.execute("SELECT id FROM projekte ORDER BY id")]
        ergebnis = []
        for projekt_id in ids:
            daten = self.projekt_daten(projekt_id)
            z = daten["zusammenfassung"]
            ergebnis.append({"id": daten["id"], "name": daten["name"],
                             "status": daten["status"],
                             "positionen": z["positionen"], "fehlen": z["fehlen"]})
        return ergebnis

    _STATUS_WORT = {"da": "da", "knapp": "knapp", "fehlt": "FEHLT",
                    "nicht_zugeordnet": "nicht zugeordnet"}

    def zeigen(self, projekt_id: int) -> str:
        """Text-BOM fürs MCP/Terminal: Kopf, dann je Baugruppe gruppierte
        Positionszeilen mit Bestandsabgleich und Preis (Stand vom Datum)."""
        daten = self.projekt_daten(projekt_id)
        z = daten["zusammenfassung"]
        kosten = f"{z['fehlteile_kosten_eur']:.4g}"
        zeilen = [f"[P-{daten['id']}] {daten['name']} — {daten['status']} · "
                 f"{z['gedeckt']} von {z['positionen']} im Bestand · "
                 f"Fehlteile ≈ {kosten} €"]

        gruppen: dict[str, list[dict]] = {}
        for pos in daten["positionen"]:
            gruppen.setdefault(pos["baugruppe"] or "Sonstiges", []).append(pos)

        for name in sorted(gruppen):
            zeilen.append(f"{name}:")
            for pos in gruppen[name]:
                info = f"{pos['menge']} benötigt"
                if pos["bestand"] is not None:
                    info += f", {pos['bestand']['menge']} im Bestand"
                    if pos["bestand"]["fach"]:
                        info += f" (Fach {pos['bestand']['fach']})"
                zeile = (f"  {pos['referenz']}  {pos['bezeichnung']} — {info} — "
                         f"{self._STATUS_WORT[pos['status']]}")
                if pos["preis"] is not None:
                    preis = pos["preis"]
                    zeile += (f" — {preis['preis_eur']:.4g} € bei {preis['quelle']}"
                              f" (Stand vom {preis['datum']})")
                zeilen.append(zeile)
        return "\n".join(zeilen)
