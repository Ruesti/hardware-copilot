"""Export-Orchestrator (E6 Task 5): Projekt → Schaltplan + PCB + Anleitung.

Schreibt in `<ausgabe_basis>/<slug>/` bis zu drei Artefakte: `<slug>.kicad_sch`
(nur wenn mindestens eine Position abgebildet werden konnte), `<slug>.kicad_pcb`
(nur wenn `pcbnew_available()`) und `anleitung.html` (immer — die Wissensbasis
hat unabhängig vom Mapping-Erfolg etwas zu sagen). Der Report fasst zusammen,
was übernommen wurde und was nicht; bei leerem Modell (alle Positionen
unabgebildet) wird kein Schaltplan geschrieben, der Report erklärt es über
`uebersprungen` statt stillen Fehlens.
"""
from __future__ import annotations

import re
from pathlib import Path

from .anleitung import baue_anleitung
from .library import load_library
from .modell import baue_export_modell
from .pcb import build_pcb, pcbnew_available
from .sch_writer import write_schematic

DEFAULT_SYMBOLS_DIR = Path("/usr/share/kicad/symbols")

_PCB_HINWEIS_KEIN_PCBNEW = (
    "pcbnew (KiCad-Python) nicht gefunden — Schaltplan und Anleitung wurden "
    "erzeugt.")


def projekt_slug(name: str) -> str:
    """Dateisystem-sicherer Ordnername aus dem Projektnamen.

    Fällt auf "projekt" zurück, wenn das Ergebnis leer ist oder nur aus
    Punkten besteht (".", "..", "..." …) — solche Namen würden sonst als
    Verzeichnis-Navigation gelesen und könnten aus `ausgabe_basis` ausbrechen
    (z. B. Projektname "..!!" → nach dem Entfernen der Sonderzeichen "..").
    """
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    if not slug or not slug.strip("."):
        return "projekt"
    return slug


def run_export(projekt: dict, wissens_repo: Path, ausgabe_basis: Path,
               symbols_dir: Path = DEFAULT_SYMBOLS_DIR, heute: str = "") -> dict:
    slug = projekt_slug(projekt["name"])
    ausgabe_basis_aufgeloest = ausgabe_basis.resolve()
    ordner = ausgabe_basis / slug
    ordner_aufgeloest = ordner.resolve()
    if (ordner_aufgeloest == ausgabe_basis_aufgeloest
            or ausgabe_basis_aufgeloest not in ordner_aufgeloest.parents):
        raise ValueError(
            f"Projekt-Slug {slug!r} bricht aus der Export-Basis "
            f"{ausgabe_basis_aufgeloest} aus — Export abgebrochen.")
    ordner.mkdir(parents=True, exist_ok=True)

    modell = baue_export_modell(projekt, load_library())

    schaltplan_pfad: Path | None = None
    if modell.instances:
        schaltplan_pfad = ordner / f"{slug}.kicad_sch"
        schaltplan_pfad.write_text(
            write_schematic(modell, symbols_dir, projekt["name"]))

    pcb_pfad: Path | None = None
    pcb_hinweis: str | None = None
    if modell.instances:
        if pcbnew_available():
            pcb_pfad = ordner / f"{slug}.kicad_pcb"
            uebersprungen_pcb = build_pcb(modell, pcb_pfad)
            for eintrag in uebersprungen_pcb:
                modell.warnings.append(
                    f"{eintrag['ref']}: {eintrag['reason']} — im PCB "
                    "übersprungen.")
        else:
            pcb_hinweis = _PCB_HINWEIS_KEIN_PCBNEW

    anleitung_pfad = ordner / "anleitung.html"
    anleitung_pfad.write_text(
        baue_anleitung(projekt, wissens_repo, heute), encoding="utf-8")

    return {
        "ordner": str(ordner),
        "schaltplan": str(schaltplan_pfad) if schaltplan_pfad else None,
        "pcb": str(pcb_pfad) if pcb_pfad else None,
        "anleitung": str(anleitung_pfad),
        "report": {
            "uebernommen": len(modell.instances),
            "uebersprungen": modell.unmapped,
            "warnungen": modell.warnings,
            "pcb_hinweis": pcb_hinweis,
        },
    }
