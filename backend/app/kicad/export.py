"""Export-Orchestrator (E6 Task 5): Projekt → Schaltplan + PCB + Anleitung.

Schreibt in `<ausgabe_basis>/<ordner_name>/` bis zu drei Artefakte:
`<ordner_name>.kicad_sch` (nur wenn mindestens eine Position abgebildet werden
konnte), `<ordner_name>.kicad_pcb` (nur wenn `pcbnew_available()`) und
`anleitung.html` (immer — die Wissensbasis hat unabhängig vom Mapping-Erfolg
etwas zu sagen). Der Report fasst zusammen, was übernommen wurde und was
nicht; bei leerem Modell (alle Positionen unabgebildet) wird kein Schaltplan
geschrieben, der Report erklärt es über `uebersprungen` statt stillen
Fehlens — genauso, wenn ein `kicad_symbol` sich nicht laden lässt (siehe
`_instanz_ladbar`).
"""
from __future__ import annotations

import re
from pathlib import Path

from .anleitung import baue_anleitung
from .library import load_library
from .modell import baue_export_modell
from .pcb import build_pcb, pcbnew_available
from .sch_writer import write_schematic
from .symbols import extract_symbol

DEFAULT_SYMBOLS_DIR = Path("/usr/share/kicad/symbols")

_PCB_HINWEIS_KEIN_PCBNEW = (
    "pcbnew (KiCad-Python) nicht gefunden — Schaltplan und Anleitung wurden "
    "erzeugt.")


def projekt_slug(name: str) -> str:
    """Dateisystem-sicherer Namens-Slug aus dem Projektnamen.

    Fällt auf "projekt" zurück, wenn das Ergebnis leer ist oder nur aus
    Punkten besteht (".", "..", "..." …) — solche Namen würden sonst als
    Verzeichnis-Navigation gelesen und könnten aus `ausgabe_basis` ausbrechen
    (z. B. Projektname "..!!" → nach dem Entfernen der Sonderzeichen "..").
    """
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    if not slug or not slug.strip("."):
        return "projekt"
    return slug


def projekt_ordner(projekt_id: int, name: str) -> str:
    """Ordner-/Dateiname für den Export, mit Projekt-ID-Präfix.

    Zwei Projekte mit unterschiedlichem Namen können auf denselben
    Namens-Slug abbilden (z. B. "Board!" und "Board?" → beide "Board"); ohne
    Präfix würden sich ihre Exporte gegenseitig überschreiben und
    `kicad-anleitung`/`kicad-oeffnen` lieferten die Artefakte des falschen
    Projekts. Router-Endpunkte müssen denselben Ordnernamen bilden — daher
    diese gemeinsame Helper-Funktion statt eigener Formatierung je Aufrufer.
    """
    return f"p{projekt_id}-{projekt_slug(name)}"


def _instanz_ladbar(lib_id: str, symbols_dir: Path) -> bool:
    """Prüft, ob `lib_id` ("<Bibliothek>:<Symbol>") aus der KiCad-Bibliothek
    ladbar ist — über denselben Loader, den `sch_writer.write_schematic`
    später für den echten Export benutzt (Bibliotheksdatei ist dort über
    `symbols._load_lib` per Bibliothek gecacht).

    Ohne diese Prüfung würde ein ungültiges `kicad_symbol` den Export erst in
    `write_schematic`/`build_pcb` crashen — als ValueError (kein Doppelpunkt),
    KeyError (Symbol nicht in der Bibliothek) oder FileNotFoundError
    (Bibliotheksdatei fehlt), jeweils ungefangen bis zum Router.
    """
    try:
        libname, symname = lib_id.split(":", 1)
        extract_symbol(libname, symname, symbols_dir)
    except (ValueError, KeyError, FileNotFoundError, OSError):
        return False
    return True


def run_export(projekt: dict, wissens_repo: Path, ausgabe_basis: Path,
               symbols_dir: Path = DEFAULT_SYMBOLS_DIR, heute: str = "") -> dict:
    ordner_name = projekt_ordner(projekt["id"], projekt["name"])
    ausgabe_basis_aufgeloest = ausgabe_basis.resolve()
    ordner = ausgabe_basis / ordner_name
    ordner_aufgeloest = ordner.resolve()
    if (ordner_aufgeloest == ausgabe_basis_aufgeloest
            or ausgabe_basis_aufgeloest not in ordner_aufgeloest.parents):
        raise ValueError(
            f"Projekt-Ordner {ordner_name!r} bricht aus der Export-Basis "
            f"{ausgabe_basis_aufgeloest} aus — Export abgebrochen.")
    ordner.mkdir(parents=True, exist_ok=True)

    modell = baue_export_modell(projekt, load_library())

    ladbar = []
    for inst in modell.instances:
        if _instanz_ladbar(inst.lib_id, symbols_dir):
            ladbar.append(inst)
        else:
            modell.unmapped.append({
                "referenz": inst.ref, "bezeichnung": inst.value,
                "grund": f"Symbol ‚{inst.lib_id}' nicht in der KiCad-Bibliothek "
                         "gefunden — kicad_symbol prüfen.",
            })
    modell.instances = ladbar

    schaltplan_pfad: Path | None = None
    if modell.instances:
        schaltplan_pfad = ordner / f"{ordner_name}.kicad_sch"
        schaltplan_pfad.write_text(
            write_schematic(modell, symbols_dir, projekt["name"]),
            encoding="utf-8")

    pcb_pfad: Path | None = None
    pcb_hinweis: str | None = None
    if modell.instances:
        if pcbnew_available():
            pcb_pfad = ordner / f"{ordner_name}.kicad_pcb"
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
