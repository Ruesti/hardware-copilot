"""Projekte-Router: dünner HTTP-Layer über bestand.projekte (Spec E5 §2).

Kein eigenes SQL, keine eigene Fachlogik — Meldungen kommen wörtlich aus dem
Dienst, damit App und MCP dieselbe Sprache sprechen. Wie bestand.py.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from bestand.projekte import ProjektDienst
from bestand.service import BestandsFehler

from ..schemas import ApiModel

router = APIRouter(prefix="/projekte", tags=["projekte"])


def _projekt_dienst() -> ProjektDienst:
    pfad = os.environ.get("BESTAND_DB", str(Path.home() / ".hardware-copilot/bestand.db"))
    return ProjektDienst(pfad)


def _ist_404(meldung: str) -> bool:
    return ("Kein Projekt" in meldung or "Kein Teil" in meldung
            or "Keine Position" in meldung)


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
