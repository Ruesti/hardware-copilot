"""Projekte-Router: dünner HTTP-Layer über bestand.projekte (Spec E5 §2).

Kein eigenes SQL, keine eigene Fachlogik — Meldungen kommen wörtlich aus dem
Dienst, damit App und MCP dieselbe Sprache sprechen. Wie bestand.py.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from bestand.projekte import ProjektDienst
from bestand.service import BestandsFehler

from ..kicad import export as kicad_export
from ..schemas import ApiModel

router = APIRouter(prefix="/projekte", tags=["projekte"])

_NOCH_KEIN_EXPORT = "Noch kein Export — erst KiCad-Export ausführen."


def _projekt_dienst() -> ProjektDienst:
    pfad = os.environ.get("BESTAND_DB", str(Path.home() / ".hardware-copilot/bestand.db"))
    return ProjektDienst(pfad)


def _wissensschicht_repo() -> Path:
    return Path(os.environ.get("WISSENSSCHICHT_REPO",
                               str(Path.home() / "projects/hardware-wissen")))


def _exporte_basis() -> Path:
    return Path(os.environ.get(
        "HARDWARE_COPILOT_EXPORTE", str(Path.home() / "hardware-copilot-exporte")
    )).expanduser()


def _ist_404(meldung: str) -> bool:
    return ("Kein Projekt" in meldung or "Kein Teil" in meldung
            or "Keine Position" in meldung)


def _projekt_oder_404(projekt_id: int) -> dict:
    try:
        return _projekt_dienst().projekt_daten(projekt_id)
    except BestandsFehler as e:
        raise HTTPException(404, str(e)) from e


class ProjektKurz(ApiModel):
    id: int
    name: str
    status: str
    positionen: int
    fehlen: int


class BestandOut(ApiModel):
    menge: int
    fach: str | None


class PreisOut(ApiModel):
    preis_eur: float
    quelle: str
    datum: str
    url: str


class PositionOut(ApiModel):
    id: int
    referenz: str
    bezeichnung: str
    menge: int
    klasse: str
    baugruppe: str
    teil_id: int | None
    pins: dict[str, str] | None
    kicad_symbol: str
    kicad_footprint: str
    notiz: str
    bestand: BestandOut | None
    status: str
    preis: PreisOut | None
    alle_preise: list[PreisOut]


class ZusammenfassungOut(ApiModel):
    positionen: int
    gedeckt: int
    fehlen: int
    fehlteile_kosten_eur: float
    ohne_preis: int


class ProjektDetail(ApiModel):
    id: int
    name: str
    beschreibung: str
    status: str
    angelegt_am: str
    positionen: list[PositionOut]
    zusammenfassung: ZusammenfassungOut


class ProjektNeu(ApiModel):
    name: str
    beschreibung: str = ""


class ZuordnenWunsch(ApiModel):
    teil_id: int


class UebersprungenOut(ApiModel):
    referenz: str
    bezeichnung: str
    grund: str


class KicadReportOut(ApiModel):
    uebernommen: int
    uebersprungen: list[UebersprungenOut]
    warnungen: list[str]
    pcb_hinweis: str | None


class KicadExportOut(ApiModel):
    ordner: str
    schaltplan: str | None
    pcb: str | None
    anleitung: str
    report: KicadReportOut


@router.get("", response_model=list[ProjektKurz], response_model_by_alias=True)
def projekte_liste():
    return _projekt_dienst().projekte_daten()


@router.get("/{projekt_id}", response_model=ProjektDetail, response_model_by_alias=True)
def projekt_detail(projekt_id: int):
    try:
        return _projekt_dienst().projekt_daten(projekt_id)
    except BestandsFehler as e:
        raise HTTPException(404, str(e)) from e


@router.post("")
def projekt_anlegen(projekt: ProjektNeu):
    d = _projekt_dienst()
    meldung = d.anlegen(projekt.name, beschreibung=projekt.beschreibung)
    neu = d.projekte_daten()[-1]
    return {"meldung": meldung, "id": neu["id"]}


@router.post("/{projekt_id}/positionen/{referenz}/zuordnen")
def position_zuordnen(projekt_id: int, referenz: str, wunsch: ZuordnenWunsch):
    try:
        meldung = _projekt_dienst().position_verknuepfen(
            projekt_id, referenz, wunsch.teil_id)
    except BestandsFehler as e:
        raise HTTPException(404 if _ist_404(str(e)) else 400, str(e)) from e
    return {"meldung": meldung}


@router.post("/{projekt_id}/abbuchen")
def projekt_abbuchen(projekt_id: int):
    try:
        meldung = _projekt_dienst().abbuchen(projekt_id)
    except BestandsFehler as e:
        raise HTTPException(404 if _ist_404(str(e)) else 400, str(e)) from e
    return {"meldung": meldung}


@router.post("/{projekt_id}/kicad-export", response_model=KicadExportOut,
             response_model_by_alias=True)
def kicad_export_endpunkt(projekt_id: int):
    projekt = _projekt_oder_404(projekt_id)
    try:
        return kicad_export.run_export(
            projekt, _wissensschicht_repo(), _exporte_basis(),
            heute=date.today().isoformat())
    except Exception as e:
        raise HTTPException(500, f"KiCad-Export fehlgeschlagen: {e}") from e


@router.get("/{projekt_id}/kicad-anleitung")
def kicad_anleitung_endpunkt(projekt_id: int):
    projekt = _projekt_oder_404(projekt_id)
    ordner_name = kicad_export.projekt_ordner(projekt["id"], projekt["name"])
    pfad = _exporte_basis() / ordner_name / "anleitung.html"
    if not pfad.exists():
        raise HTTPException(404, _NOCH_KEIN_EXPORT)
    return FileResponse(pfad, media_type="text/html")


@router.post("/{projekt_id}/kicad-oeffnen")
def kicad_oeffnen_endpunkt(projekt_id: int):
    projekt = _projekt_oder_404(projekt_id)
    ordner_name = kicad_export.projekt_ordner(projekt["id"], projekt["name"])
    schaltplan = _exporte_basis() / ordner_name / f"{ordner_name}.kicad_sch"
    if not schaltplan.exists():
        raise HTTPException(400, _NOCH_KEIN_EXPORT)
    xdg_open = shutil.which("xdg-open")
    if not xdg_open:
        raise HTTPException(400, "xdg-open nicht verfügbar")
    subprocess.Popen([xdg_open, str(schaltplan)])
    return {"meldung": f"KiCad-Öffnen angestoßen: {schaltplan}"}
