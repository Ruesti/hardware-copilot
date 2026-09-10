"""Bestand-Router: dünner HTTP-Layer über bestand.service (Spec §3.4).

Kein eigenes SQL, keine eigene Fachlogik — Meldungen kommen wörtlich aus dem
Dienst, damit App und MCP dieselbe Sprache sprechen.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from bestand.service import BestandsDienst, BestandsFehler

from ..schemas import ApiModel

router = APIRouter(prefix="/bestand", tags=["bestand"])


def _dienst() -> BestandsDienst:
    pfad = os.environ.get("BESTAND_DB", str(Path.home() / ".hardware-copilot/bestand.db"))
    return BestandsDienst(pfad, regal_url=os.environ.get("BESTAND_REGAL_URL"))


class TeilKurz(ApiModel):
    id: int
    bezeichnung: str
    menge: int
    klasse: str
    hersteller_nr: str
    fach: str | None


class PreisEintrag(ApiModel):
    quelle: str
    preis_eur: float
    url: str
    datum: str


class AlternativeEintrag(ApiModel):
    bezeichnung: str
    hersteller_nr: str
    hinweis: str
    datum: str


class TeilDetail(ApiModel):
    id: int
    bezeichnung: str
    hersteller_nr: str
    klasse: str
    menge: int
    eckdaten: str
    datenblatt_url: str
    fach: str | None
    alternativen: list[AlternativeEintrag]
    preise: list[PreisEintrag]


class TeilNeu(ApiModel):
    bezeichnung: str
    menge: int
    fach: str
    klasse: str = ""
    hersteller_nr: str = ""
    eckdaten: str = ""
    datenblatt_url: str = ""


class MengenDelta(ApiModel):
    delta: int


class LeuchtWunsch(ApiModel):
    farbe: str = "gruen"
    dauer_s: int = 30


@router.get("/teile", response_model=list[TeilKurz], response_model_by_alias=True)
def teile_liste(suche: str = "", klasse: str | None = None):
    return _dienst().suche_daten(suche, klasse=klasse)


@router.get("/teile/{teil_id}", response_model=TeilDetail, response_model_by_alias=True)
def teil_detail(teil_id: int):
    try:
        return _dienst().teil_daten(teil_id)
    except BestandsFehler as e:
        raise HTTPException(404, str(e)) from e


@router.post("/teile")
def teil_anlegen(teil: TeilNeu):
    d = _dienst()
    try:
        meldung = d.anlegen(teil.bezeichnung, menge=teil.menge, fach=teil.fach,
                            klasse=teil.klasse, hersteller_nr=teil.hersteller_nr,
                            eckdaten=teil.eckdaten, datenblatt_url=teil.datenblatt_url)
    except BestandsFehler as e:
        raise HTTPException(400, str(e)) from e
    neu = d.suche_daten()[-1]
    return {"meldung": meldung, "id": neu["id"]}


@router.patch("/teile/{teil_id}/menge")
def menge_aendern(teil_id: int, delta: MengenDelta):
    d = _dienst()
    try:
        meldung = d.menge_aendern(teil_id, delta.delta)
    except BestandsFehler as e:
        raise HTTPException(404 if "Kein Teil" in str(e) else 400, str(e)) from e
    return {"meldung": meldung, "menge": d.teil_daten(teil_id)["menge"]}


@router.post("/teile/{teil_id}/leuchten")
def fach_leuchten(teil_id: int, wunsch: LeuchtWunsch):
    try:
        return {"meldung": _dienst().fach_leuchten(
            teil_id, farbe=wunsch.farbe, dauer_s=wunsch.dauer_s)}
    except BestandsFehler as e:
        raise HTTPException(404 if "Kein Teil" in str(e) else 400, str(e)) from e


@router.get("/klassen")
def klassen():
    return _dienst().klassen_daten()
