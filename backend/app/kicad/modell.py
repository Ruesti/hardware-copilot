"""Export-Modell (E6): Dataclasses aus dem alten netlist.py + Modell-Bauer,
der aus Projekt-Positionen (E5) ein ExportModel für den KiCad-Export macht."""
from __future__ import annotations

from dataclasses import dataclass, field

from .library import Library


@dataclass
class SymbolInstance:
    ref: str
    lib_id: str
    value: str
    footprint: str
    block_name: str
    pin_nets: dict[str, str]
    status: str  # "mapped" | "fallback" | "unverified"
    name: str = ""
    component_id: str = ""
    net_role: str | None = None


@dataclass
class ExportModel:
    instances: list[SymbolInstance] = field(default_factory=list)
    unmapped: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def baue_export_modell(projekt: dict, library: Library) -> ExportModel:
    """Baut das Export-Modell aus den Positionen eines Projekts (E5).

    Kaskade für das Symbol: explizites `kicad_symbol` gewinnt; sonst wird die
    Bibliothek über die Hersteller-Nr. des verknüpften Teils befragt; ohne
    Treffer landet die Position unabgebildet im Report (`unmapped`) und
    bekommt keine Instanz. Das Footprint folgt derselben Priorität, fehlt es
    ganz bleibt es leer.
    """
    modell = ExportModel()
    for position in projekt["positionen"]:
        referenz = position["referenz"]
        bezeichnung = position["bezeichnung"]
        bestand = position.get("bestand") or {}
        teil = library.for_component(bestand.get("hersteller_nr"), None)

        kicad_symbol = position.get("kicad_symbol") or ""
        if kicad_symbol:
            lib_id = kicad_symbol
        elif teil is not None:
            lib_id = teil.lib_id
        else:
            modell.unmapped.append({
                "referenz": referenz, "bezeichnung": bezeichnung,
                "grund": "kein KiCad-Symbol — kicad_symbol angeben oder Teil "
                         "in parts.yaml aufnehmen"})
            continue

        kicad_footprint = position.get("kicad_footprint") or ""
        footprint = kicad_footprint or (teil.footprint if teil is not None else "")

        pin_nets = position.get("pins") or {}
        modell.instances.append(SymbolInstance(
            ref=referenz, lib_id=lib_id, value=bezeichnung, footprint=footprint,
            block_name=position.get("baugruppe") or "Sonstiges",
            pin_nets=pin_nets, status="mapped", name=bezeichnung))

        menge = position["menge"]
        if menge > 1:
            modell.warnings.append(
                f"{referenz}: Menge {menge} — im Schaltplan ein Symbol je "
                "Referenz; für mehrere Exemplare eigene Referenzen anlegen.")
        if not pin_nets:
            modell.warnings.append(
                f"{referenz}: keine Pin-Netze — Symbol wird unverdrahtet "
                "platziert.")

    return modell
