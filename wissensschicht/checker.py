"""C2-Klassifikations-Prüfung: vorgeschlagene Stufen validieren, nur abstufen.

Obergrenze des Regel-Teils ist die in den Daten gespeicherte Stufe der Regel;
der Anwendungs-Teil (Herleitung auf den konkreten Fall) ist strukturell auf
*vermutung* gedeckelt (§0 C3).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .store import Regel

_RANG = {"vermutung": 0, "verifiziert": 1, "belegt": 2}


class UnbekannteRegel(Exception):
    pass


@dataclass
class PruefErgebnis:
    regel_stufe: str
    anwendung_stufe: str
    korrekturen: list[str] = field(default_factory=list)


def check_hint(regeln: dict[str, Regel], regel_id: str,
               regel_stufe: str, anwendung_stufe: str) -> PruefErgebnis:
    if regel_id not in regeln:
        raise UnbekannteRegel(f"Regel {regel_id} existiert nicht in der Regelbasis")
    gespeichert = regeln[regel_id].stufe
    korrekturen: list[str] = []

    if _RANG[regel_stufe] > _RANG[gespeichert]:
        korrekturen.append(
            f"Regel-Teil {regel_id}: {regel_stufe} auf {gespeichert} abgestuft "
            f"(gespeicherte Stufe ist die Obergrenze)")
        regel_stufe = gespeichert

    if anwendung_stufe != "vermutung":
        korrekturen.append(
            f"Anwendungs-Teil: {anwendung_stufe} auf vermutung abgestuft "
            f"(Herleitung auf den konkreten Fall ist nie mehr als Vermutung, C3)")
        anwendung_stufe = "vermutung"

    return PruefErgebnis(regel_stufe=regel_stufe, anwendung_stufe=anwendung_stufe,
                         korrekturen=korrekturen)
