"""Wissen-Router: read-only Sicht aufs Wissens-Repo (Regeln, Blocks, Lücken).

Dieselben Dateien, die die Wissensschicht der KI serviert — nur als JSON
fürs Panel. Stufen sind Daten; das Frontend zeigt sie unverändert an.
"""
from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException

from wissensschicht.blocks import block_volltext, lade_bloecke
from wissensschicht.gaps import list_gaps
from wissensschicht.store import StoreError, load_rules

router = APIRouter(prefix="/wissen", tags=["wissen"])


def _repo() -> Path:
    return Path(os.environ.get("WISSENSSCHICHT_REPO",
                               str(Path.home() / "projects/hardware-wissen")))


def _regeln():
    try:
        return load_rules(_repo())
    except StoreError as e:
        raise HTTPException(503, f"Wissens-Repo fehlerhaft: {e}") from e


@router.get("/regeln")
def regeln(klasse: str | None = None, stufe: str | None = None):
    ergebnis = []
    for r in _regeln():
        if klasse and r.geltung.get("klasse") != klasse:
            continue
        if stufe and r.stufe != stufe:
            continue
        ergebnis.append({"id": r.id, "bereich": r.bereich, "aussage": r.aussage,
                         "staerke": r.staerke, "stufe": r.stufe,
                         "klasse": r.geltung.get("klasse", "")})
    return ergebnis


@router.get("/regeln/{regel_id}")
def regel(regel_id: str):
    for r in _regeln():
        if r.id == regel_id:
            return asdict(r)
    raise HTTPException(404, f"Keine Regel {regel_id}.")


@router.get("/klassen")
def klassen():
    return sorted({r.geltung.get("klasse", "") for r in _regeln()} - {""})


@router.get("/bloecke")
def bloecke():
    return [{"id": b.id, "titel": b.titel, "kernbauteil": b.kernbauteil,
             "topologie": b.topologie} for b in lade_bloecke(_repo())]


@router.get("/bloecke/{block_id}")
def block(block_id: str):
    for b in lade_bloecke(_repo()):
        if b.id == block_id:
            return {**asdict(b), "volltext": block_volltext(b)}
    raise HTTPException(404, f"Kein Block {block_id}.")


@router.get("/luecken")
def luecken():
    return list_gaps(_repo() / "luecken.md")
