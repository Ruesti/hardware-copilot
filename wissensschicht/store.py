"""Regelbasis laden: eine TOML-Datei pro Regel, Schema siehe SCHEMA.md im Wissens-Repo.

Validierung erzwingt die Kern-Invariante aus §0 Block B3/C2: *belegt* existiert nur
mit vollständiger Primärquelle, *vermutung* nie mit Primärquellen-Typ.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

PRIMAERQUELLEN = {"datenblatt", "applikationsschrift", "norm"}
SEKUNDAERQUELLEN = {"buch", "video", "keine"}
STUFEN = {"belegt", "verifiziert", "vermutung"}
STAERKEN = {"muss", "sollte", "kann"}
PFLICHTFELDER = ("id", "bereich", "aussage", "begruendung", "staerke", "stufe",
                 "datum_eintrag", "datum_geprueft", "ausnahmen", "quelle", "geltung")


class StoreError(Exception):
    """Regelbasis verletzt das Schema — Server darf so nicht starten."""


@dataclass(frozen=True)
class Regel:
    id: str
    bereich: str
    aussage: str
    begruendung: str
    staerke: str
    stufe: str
    datum_eintrag: str
    datum_geprueft: str
    ausnahmen: list[str]
    quelle: dict
    geltung: dict


def _validiere(d: dict, datei: str) -> None:
    for feld in PFLICHTFELDER:
        if feld not in d:
            raise StoreError(f"{datei}: Pflichtfeld fehlt: {feld}")
    if d["stufe"] not in STUFEN:
        raise StoreError(f"{datei}: ungültige stufe: {d['stufe']}")
    if d["staerke"] not in STAERKEN:
        raise StoreError(f"{datei}: ungültige staerke: {d['staerke']}")
    if "klasse" not in d["geltung"]:
        raise StoreError(f"{datei}: geltung.klasse fehlt (Pflichtachse)")
    q = d["quelle"]
    if d["stufe"] == "belegt":
        if q.get("typ") not in PRIMAERQUELLEN:
            raise StoreError(f"{datei}: belegt erfordert Primärquelle, hat typ={q.get('typ')}")
        for feld in ("titel", "fundstelle", "url", "zitat"):
            if not q.get(feld):
                raise StoreError(f"{datei}: belegt ohne quelle.{feld}")
    elif d["stufe"] == "vermutung":
        if q.get("typ") not in SEKUNDAERQUELLEN:
            raise StoreError(f"{datei}: vermutung darf keinen Primärquellen-typ tragen ({q.get('typ')})")


def load_rules(wissens_repo: Path) -> list[Regel]:
    """Lädt alle Regeln aus <wissens_repo>/regeln/**/R-*.toml. Wirft StoreError bei Schema-Verstoß."""
    regeln: list[Regel] = []
    ids: set[str] = set()
    for datei in sorted(Path(wissens_repo).glob("regeln/*/R-*.toml")):
        try:
            d = tomllib.loads(datei.read_text())
        except tomllib.TOMLDecodeError as e:
            raise StoreError(f"{datei.name}: TOML-Syntaxfehler: {e}") from e
        _validiere(d, datei.name)
        if d["id"] in ids:
            raise StoreError(f"{datei.name}: doppelte id {d['id']}")
        ids.add(d["id"])
        regeln.append(Regel(
            id=d["id"], bereich=d["bereich"], aussage=d["aussage"],
            begruendung=d["begruendung"], staerke=d["staerke"], stufe=d["stufe"],
            datum_eintrag=str(d["datum_eintrag"]), datum_geprueft=str(d["datum_geprueft"]),
            ausnahmen=list(d["ausnahmen"]), quelle=dict(d["quelle"]), geltung=dict(d["geltung"]),
        ))
    return regeln
