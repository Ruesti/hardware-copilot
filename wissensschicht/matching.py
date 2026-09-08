"""Geltungs-Match: Bedingungsfelder einer Regel gegen einen erzählten Fall (§0 A3/B2).

Semantik:
- `klasse` ist Pflichtachse: die Regel trifft nur, wenn ihre Klasse unter den
  Fall-Klassen ist.
- Jede weitere Regel-Achse muss dem Fall-Wert gleichen, WENN der Fall sie angibt.
- Gibt der Fall eine Regel-Achse nicht an, trifft die Regel trotzdem — die
  Bedingung wird aber als unbestätigt zurückgemeldet (C3-Ehrlichkeit: die
  Anwendbarkeit ist dann nicht vollständig geprüft).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .store import Regel


@dataclass(frozen=True)
class Treffer:
    regel: Regel
    unbestaetigt: list[str] = field(default_factory=list)


def match_rules(regeln: list[Regel], fall: dict) -> list[Treffer]:
    fall_klassen = set(fall.get("klasse", []))
    treffer: list[Treffer] = []
    for regel in regeln:
        if regel.geltung["klasse"] not in fall_klassen:
            continue
        unbestaetigt: list[str] = []
        passt = True
        for achse, wert in regel.geltung.items():
            if achse == "klasse":
                continue
            if achse in fall:
                if fall[achse] != wert:
                    passt = False
                    break
            else:
                unbestaetigt.append(f"{achse}={wert}")
        if passt:
            treffer.append(Treffer(regel=regel, unbestaetigt=unbestaetigt))
    return treffer
