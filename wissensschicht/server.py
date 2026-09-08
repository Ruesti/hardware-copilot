"""MCP-Server der Wissensschicht (§0 Phase 2): rein auf Abruf, nur lesend.

Start:  python -m wissensschicht.server
Konfiguration: WISSENSSCHICHT_REPO zeigt aufs Wissens-Repo
(Default: ~/projects/hardware-wissen).
"""
from __future__ import annotations

import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from .service import WissensDienst

mcp = MCPServer("wissensschicht")


def _dienst() -> WissensDienst:
    repo = os.environ.get("WISSENSSCHICHT_REPO", str(Path.home() / "projects/hardware-wissen"))
    return WissensDienst(Path(repo))


@mcp.tool()
def query_rules(klassen: list[str], achsen: dict | None = None,
                frage: str | None = None) -> str:
    """Regeln zu einem beschriebenen Schaltungsfall abrufen (Kurzform: ID, Stufe, Aussage).

    klassen: Bauteil-/Schaltungsklassen des Falls, z. B. ["schaltregler", "mcu_wifi"].
    Gültige Werte stehen im Achsenkatalog des Wissens-Repos (SCHEMA.md).
    achsen: weitere Fall-Eigenschaften, z. B. {"last_typ": "induktiv"}. Bedingungen,
    die der Fall nicht angibt, werden als unbestätigt gemeldet.
    WICHTIG: Spannung und Strom des Falls immer mit angeben, wenn bekannt —
    {"spannung_v": 230, "strom_a": 2.0} — sie steuern die Heikel-Erkennung
    (§0 Block E): heikle Bereiche liefern eine Frage statt einer Anweisung.
    frage: Freitext dessen, was beantwortet werden soll — wird bei leerem Ergebnis
    ins Lücken-Protokoll übernommen (C6).
    Details zu einer Regel liefert get_rule; Stufen sind Daten des Servers und
    dürfen vom Modell nie erhöht werden.
    """
    return _dienst().query(klassen=klassen, achsen=achsen, frage=frage)


@mcp.tool()
def get_rule(regel_id: str) -> str:
    """Volltext einer Regel: Aussage, Begründung, Stärke, Stufe, Quelle mit
    Fundstelle und wörtlichem Zitat, Geltungsbereich, Ausnahmen — als Markdown
    mit eingebettetem JSON. Den Markdown-Block unverändert an den Nutzer
    durchreichen; Stufen-Marker (⚠ VERMUTUNG) nicht entfernen oder umformulieren."""
    return _dienst().regel(regel_id)


@mcp.tool()
def check_hint(regel_id: str, regel_stufe: str, anwendung_stufe: str) -> str:
    """Eigenen Hinweis-Entwurf prüfen lassen, BEVOR er dem Nutzer gezeigt wird.

    Ein Hinweis besteht aus Regel-Teil (zitierte Regel) und Anwendungs-Teil
    (Herleitung auf den konkreten Fall). Der Server validiert die vorgeschlagenen
    Stufen und stuft nur ab, nie hoch: Obergrenze des Regel-Teils ist die
    gespeicherte Stufe, der Anwendungs-Teil ist immer höchstens vermutung."""
    return _dienst().pruefe(regel_id, regel_stufe=regel_stufe, anwendung_stufe=anwendung_stufe)


@mcp.tool()
def report_gap(frage: str, grund: str) -> str:
    """Wissenslücke ins Lücken-Protokoll eintragen (C6) — z. B. wenn eine
    Nutzerfrage nur mit Vermutungen beantwortet werden konnte. Jeder Eintrag
    ist Kandidat für eine neue Regel mit Quelle."""
    return _dienst().melde_luecke(frage=frage, grund=grund)


@mcp.tool()
def list_gaps() -> str:
    """Lücken-Protokoll auflisten: offene Fragen ohne belegte Regel."""
    eintraege = _dienst().luecken()
    if not eintraege:
        return "Lücken-Protokoll ist leer."
    return "\n".join(f"- {e['datum']}: {e['frage']} ({e['grund']}) — {e['status']}"
                     for e in eintraege)


@mcp.tool()
def record_block(titel: str, kernbauteil: str, topologie: str, gebaut: str,
                 gemessen: str, messbedingungen: str, grenzen: str, projekt: str,
                 ausschnitt: str, gescheitert: str = "", fallback: str = "",
                 revision: str = "", regeln: list[str] | None = None) -> str:
    """Einen real aufgebauten und vermessenen Schaltungsblock als Verified Block
    erfassen (§0 Phase 4). NUR nach echtem Aufbau mit echten Messwerten aufrufen —
    nie für geplante oder simulierte Schaltungen.

    Pflicht: titel, kernbauteil, topologie, gebaut (Bauteile mit Werten), gemessen
    (Zahlen!), messbedingungen (womit/wie gemessen), grenzen (bis wohin getestet),
    projekt, ausschnitt (Teilschaltbild/Netzliste als Text — wird eingefroren, D3).
    Optional: gescheitert, fallback, revision, regeln (Regel-IDs, die dieser
    Aufbau stützt — Hochstufen auf verifiziert macht der Mensch im Wissens-Repo, C5)."""
    return _dienst().erfasse_block(
        titel=titel, kernbauteil=kernbauteil, topologie=topologie, gebaut=gebaut,
        gemessen=gemessen, gescheitert=gescheitert, fallback=fallback,
        projekt=projekt, messbedingungen=messbedingungen, grenzen=grenzen,
        revision=revision, ausschnitt=ausschnitt, regeln=regeln)


@mcp.tool()
def search_blocks(suchbegriff: str) -> str:
    """Verified Blocks durchsuchen (Kernbauteil, Titel, Topologie). Liefert real
    vermessene Aufbauten als Referenz. ⚠ D4: verifiziert gilt exakt für den
    erfassten Aufbau innerhalb seiner getesteten Grenzen — die Übertragung auf
    einen ähnlichen Fall ist eine Vermutung und braucht eine explizite
    Differenzliste der Abweichungen."""
    return _dienst().bloecke_suchen(suchbegriff)


@mcp.tool()
def get_block(block_id: str) -> str:
    """Volltext eines Verified Blocks: was gebaut, was gemessen (mit Bedingungen
    und Grenzen), was gescheitert, Fallback, eingefrorener Ausschnitt, verknüpfte
    Regeln — inklusive D4-Hinweis zur Übertragbarkeit."""
    return _dienst().block(block_id)


if __name__ == "__main__":
    mcp.run()
