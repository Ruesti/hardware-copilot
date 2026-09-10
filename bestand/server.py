"""MCP-Server des Bestands (Etappe E1): Bestands-DB abfragen und pflegen.

Start:  python -m bestand.server
Konfiguration: BESTAND_DB — Pfad zur SQLite-Datei
(Default: ~/.hardware-copilot/bestand.db); BESTAND_REGAL_URL — optional,
ohne sie meldet fach_leuchten nur das Fach.
"""
from __future__ import annotations

import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from .service import BestandsDienst, BestandsFehler

mcp = MCPServer("bestand")


def _dienst() -> BestandsDienst:
    pfad = os.environ.get("BESTAND_DB", str(Path.home() / ".hardware-copilot/bestand.db"))
    return BestandsDienst(pfad, regal_url=os.environ.get("BESTAND_REGAL_URL"))


def _antwort(aufruf) -> str:
    try:
        return aufruf()
    except BestandsFehler as e:
        return f"⚠ {e}"


@mcp.tool()
def teil_suchen(suchbegriff: str, klasse: str | None = None) -> str:
    """Bestand durchsuchen: Welche Bauteile habe ich da?

    suchbegriff: Teilstring über Bezeichnung, Hersteller-Nummer und Eckdaten
    (z. B. "100nF", "TPS54331"). Exakte Teil-ID "T-3" liefert stattdessen den
    Volltext mit Alternativen und Preisen (Preise immer mit Stand-Datum —
    ältere Preise nie als aktuell ausgeben).
    klasse: optionaler Filter; gleiche Klassen wie im Achsenkatalog des
    Wissens-Repos (SCHEMA.md), z. B. schaltregler, abblock_c, mcu_wifi."""
    return _antwort(lambda: _dienst().suchen(suchbegriff, klasse=klasse))


@mcp.tool()
def teil_anlegen(bezeichnung: str, menge: int, fach: str, klasse: str = "",
                 hersteller_nr: str = "", eckdaten: str = "",
                 datenblatt_url: str = "") -> str:
    """Neues Bauteil im Bestand anlegen.

    fach: Regal/Position, z. B. "A/3" — unbekannte Fächer werden automatisch
    angelegt. klasse: möglichst aus dem Achsenkatalog des Wissens-Repos wählen,
    damit Bestand und Wissensschicht dieselbe Sprache sprechen."""
    return _antwort(lambda: _dienst().anlegen(
        bezeichnung, menge=menge, fach=fach, klasse=klasse,
        hersteller_nr=hersteller_nr, eckdaten=eckdaten,
        datenblatt_url=datenblatt_url))


@mcp.tool()
def menge_aendern(teil_id: int, delta: int) -> str:
    """Bestandsmenge relativ ändern: delta +5 = zugekauft, -2 = verbraucht.
    Unter 0 wird abgelehnt (mit aktuellem Bestand in der Meldung)."""
    return _antwort(lambda: _dienst().menge_aendern(teil_id, delta))


@mcp.tool()
def alternative_vermerken(teil_id: int, bezeichnung: str,
                          hersteller_nr: str = "", hinweis: str = "") -> str:
    """Austausch-Bauteil zu einem Bestandsteil vermerken (z. B. nach Recherche):
    erscheint im Teil-Volltext (teil_suchen mit "T-<id>")."""
    return _antwort(lambda: _dienst().alternative_vermerken(
        teil_id, bezeichnung, hersteller_nr=hersteller_nr, hinweis=hinweis))


@mcp.tool()
def preis_cachen(teil_id: int, quelle: str, preis_eur: float, url: str = "") -> str:
    """Recherchierten Preis zum Teil ablegen. Das Datum setzt der Server;
    Preise werden immer mit „Stand vom <datum>“ ausgegeben, weil sie veralten."""
    return _antwort(lambda: _dienst().preis_cachen(
        teil_id, quelle, preis_eur, url=url))


@mcp.tool()
def fach_leuchten(teil_id: int, farbe: str = "gruen", dauer_s: int = 30) -> str:
    """Das Regal-Fach eines Teils aufleuchten lassen (gruen = hier liegt dein
    Teil, blau = hier einsortieren). Ohne konfiguriertes Regal
    (BESTAND_REGAL_URL) wird nur das Fach genannt — auch das beantwortet
    „wo liegt das Teil?“."""
    return _antwort(lambda: _dienst().fach_leuchten(
        teil_id, farbe=farbe, dauer_s=dauer_s))


if __name__ == "__main__":
    mcp.run()
