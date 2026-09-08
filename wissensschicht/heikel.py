"""Block-E-Heikel-Mechanik (§0 E1-E4): heikle Bereiche bekommen eine Frage statt einer Anweisung.

Die Inhalte (Fragen im E3-Stil, Fundstellen, Schwellen) leben als heikel.toml im
Wissens-Repo; hier steht nur die Auswertung. Auslösung nach E2 doppelt: über
Klassen-/Achsen-Flags UND strukturelle Schwellen (numerische Fall-Achsen
spannung_v / strom_a) — damit greift die Frage auch dort, wo gar keine Regel
existiert (C6-Fall).
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class HeikelBereich:
    name: str
    frage: str
    fundstelle: str = ""
    fundstelle_hinweis: str = ""
    unterdrueckt_regeln: bool = False
    regel_unterdrueckung_grund: str = ""
    klassen: list[str] = field(default_factory=list)
    achsen_trigger: dict = field(default_factory=dict)
    spannung_min_v: float | None = None
    strom_min_a: float | None = None


def lade_heikel(repo: Path) -> list[HeikelBereich]:
    datei = Path(repo) / "heikel.toml"
    if not datei.exists():
        return []
    d = tomllib.loads(datei.read_text())
    return [HeikelBereich(
        name=b["name"], frage=b["frage"],
        fundstelle=b.get("fundstelle", ""),
        fundstelle_hinweis=b.get("fundstelle_hinweis", ""),
        unterdrueckt_regeln=b.get("unterdrueckt_regeln", False),
        regel_unterdrueckung_grund=b.get("regel_unterdrueckung_grund", ""),
        klassen=list(b.get("klassen", [])),
        achsen_trigger=dict(b.get("achsen_trigger", {})),
        spannung_min_v=b.get("spannung_min_v"),
        strom_min_a=b.get("strom_min_a"),
    ) for b in d.get("bereich", [])]


def _triggert(b: HeikelBereich, fall: dict) -> bool:
    if b.klassen and set(b.klassen) & set(fall.get("klasse", [])):
        return True
    if b.achsen_trigger and all(fall.get(a) == w for a, w in b.achsen_trigger.items()):
        return True
    if b.spannung_min_v is not None and isinstance(fall.get("spannung_v"), (int, float)) \
            and fall["spannung_v"] >= b.spannung_min_v:
        return True
    if b.strom_min_a is not None and isinstance(fall.get("strom_a"), (int, float)) \
            and fall["strom_a"] >= b.strom_min_a:
        return True
    return False


def pruefe_heikel(bereiche: list[HeikelBereich], fall: dict) -> list[HeikelBereich]:
    return [b for b in bereiche if _triggert(b, fall)]
