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

from .projekte import ProjektDienst
from .service import BestandsDienst, BestandsFehler

mcp = MCPServer("bestand")


def _dienst() -> BestandsDienst:
    pfad = os.environ.get("BESTAND_DB", str(Path.home() / ".hardware-copilot/bestand.db"))
    return BestandsDienst(pfad, regal_url=os.environ.get("BESTAND_REGAL_URL"))


def _projekt_dienst() -> ProjektDienst:
    pfad = os.environ.get("BESTAND_DB", str(Path.home() / ".hardware-copilot/bestand.db"))
    return ProjektDienst(pfad)


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


@mcp.tool()
def projekt_anlegen(name: str, beschreibung: str = "") -> str:
    """Neues Projekt (Schaltungsentwurf/Baugruppe) anlegen — der Rahmen für
    seine Stückliste. Positionen kommen danach über position_hinzufuegen dazu."""
    return _antwort(lambda: _projekt_dienst().anlegen(name, beschreibung=beschreibung))


@mcp.tool()
def position_hinzufuegen(projekt_id: int, referenz: str, bezeichnung: str,
                         menge: int = 1, klasse: str = "",
                         teil_id: int | None = None, baugruppe: str = "",
                         pins: dict | None = None, kicad_symbol: str = "",
                         kicad_footprint: str = "", notiz: str = "") -> str:
    """Stückliste-Position zu einem Projekt hinzufügen.

    referenz: Bezeichner wie im Schaltplan, z. B. "C3", "U1" — muss je Projekt
    eindeutig sein. pins: Pin→Netz-Zuordnung (z. B. {"1": "GND", "2": "VCC"}),
    fürs spätere KiCad gedacht. klasse: möglichst aus dem Achsenkatalog des
    Wissens-Repos wählen. teil_id: verknüpft die Position sofort mit einem
    Bestandsteil (T-<id>) — alternativ später über position_verknuepfen.
    kicad_symbol/kicad_footprint: mitgeben, sobald bekannt, für die spätere
    KiCad-Brücke."""
    return _antwort(lambda: _projekt_dienst().position_hinzufuegen(
        projekt_id, referenz, bezeichnung, menge=menge, klasse=klasse,
        teil_id=teil_id, baugruppe=baugruppe, pins=pins,
        kicad_symbol=kicad_symbol, kicad_footprint=kicad_footprint,
        notiz=notiz))


@mcp.tool()
def position_verknuepfen(projekt_id: int, referenz: str, teil_id: int) -> str:
    """Bestehende Stückliste-Position nachträglich mit einem Bestandsteil
    (T-<id>) verknüpfen, z. B. nachdem das passende Teil gefunden wurde."""
    return _antwort(lambda: _projekt_dienst().position_verknuepfen(
        projekt_id, referenz, teil_id))


@mcp.tool()
def projekt_zeigen(projekt_id: int) -> str:
    """Stückliste eines Projekts mit Bestandsabgleich anzeigen: je Baugruppe
    gruppierte Positionen, ob das Teil im Bestand da/knapp/fehlt ist, Fach
    und — bei Fehlteilen — Preis (Stand vom Datum) und geschätzte Kosten."""
    return _antwort(lambda: _projekt_dienst().zeigen(projekt_id))


@mcp.tool()
def projekt_abbuchen(projekt_id: int) -> str:
    """Alle mit einem Bestandsteil verknüpften Positionen aus dem Bestand
    abbuchen und das Projekt abschließen. Reicht der Bestand für irgendeine
    Position nicht, wird nichts gebucht (Unterdeckungs-Schutz) — die Meldung
    nennt die fehlenden Referenzen und Mengen. Nicht verknüpfte Positionen
    werden übersprungen und in der Meldung genannt."""
    return _antwort(lambda: _projekt_dienst().abbuchen(projekt_id))


if __name__ == "__main__":
    mcp.run()
