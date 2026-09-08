"""Phase 4: Verified Blocks — real vermessene Aufbauten erfassen und nachschlagen.

§0-Entscheidungen: Ein Block ist eine konkrete Bauteil-Kombination mit Werten (D1),
erfasst mit vollem Feldschema inkl. Messbedingungen und getesteter Grenzen (D2),
verankert als eingefrorener Ausschnitt neben der TOML-Datei (D3). Übertragung auf
ähnliche Fälle ist immer Vermutung plus Differenzliste (D4). Stufenwechsel von
Regeln (vermutung -> verifiziert) löst der Mensch im Wissens-Repo aus, nie der
Server (C5) — das Erfassen liefert dafür nur den Hinweis.

Das Schema ist laut D5 vorläufig; Revision nach den ersten echten Blöcken ist
eingeplant und kein Scheitern.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

PFLICHT_NICHT_LEER = ("titel", "kernbauteil", "topologie", "gebaut", "gemessen",
                      "projekt", "messbedingungen", "grenzen", "ausschnitt")


class BlockFehler(Exception):
    pass


@dataclass(frozen=True)
class Block:
    id: str
    titel: str
    kernbauteil: str
    topologie: str
    gebaut: str
    gemessen: str
    gescheitert: str
    fallback: str
    datum: str
    projekt: str
    messbedingungen: str
    grenzen: str
    revision: str
    ausschnitt_datei: str
    regeln: list[str] = field(default_factory=list)


def _bloecke_dir(repo: Path) -> Path:
    d = Path(repo) / "bloecke"
    d.mkdir(parents=True, exist_ok=True)
    return d


def lade_bloecke(repo: Path) -> list[Block]:
    bloecke = []
    for datei in sorted(_bloecke_dir(repo).glob("B-*.toml")):
        d = tomllib.loads(datei.read_text())
        bloecke.append(Block(**d))
    return bloecke


def _naechste_id(repo: Path) -> str:
    nummern = [int(f.stem.split("-")[1]) for f in _bloecke_dir(repo).glob("B-*.toml")]
    return f"B-{max(nummern, default=0) + 1:03d}"


def _toml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def erfasse_block(repo: Path, *, titel: str, kernbauteil: str, topologie: str,
                  gebaut: str, gemessen: str, gescheitert: str, fallback: str,
                  projekt: str, messbedingungen: str, grenzen: str, revision: str,
                  ausschnitt: str, regeln: list[str] | None = None) -> str:
    werte = dict(titel=titel, kernbauteil=kernbauteil, topologie=topologie,
                 gebaut=gebaut, gemessen=gemessen, projekt=projekt,
                 messbedingungen=messbedingungen, grenzen=grenzen, ausschnitt=ausschnitt)
    for feld in PFLICHT_NICHT_LEER:
        if not werte.get(feld, "").strip():
            raise BlockFehler(f"Pflichtfeld leer: {feld} — ein Verified Block ohne {feld} "
                              "wäre kein Nachweis (§0 D2)")
    regeln = regeln or []
    block_id = _naechste_id(repo)
    ausschnitt_datei = f"{block_id}-ausschnitt.txt"
    d = _bloecke_dir(repo)
    (d / ausschnitt_datei).write_text(ausschnitt)
    zeilen = [f"id = {_toml_str(block_id)}"]
    for feld, wert in [("titel", titel), ("kernbauteil", kernbauteil),
                       ("topologie", topologie), ("gebaut", gebaut),
                       ("gemessen", gemessen), ("gescheitert", gescheitert),
                       ("fallback", fallback), ("datum", str(date.today())),
                       ("projekt", projekt), ("messbedingungen", messbedingungen),
                       ("grenzen", grenzen), ("revision", revision),
                       ("ausschnitt_datei", ausschnitt_datei)]:
        zeilen.append(f"{feld} = {_toml_str(wert)}")
    zeilen.append("regeln = [" + ", ".join(_toml_str(r) for r in regeln) + "]")
    (d / f"{block_id}.toml").write_text("\n".join(zeilen) + "\n")

    meldung = [f"Verified Block {block_id} erfasst ({titel}); Ausschnitt eingefroren in {ausschnitt_datei}."]
    if regeln:
        meldung.append(
            f"Verknüpfte Regeln: {', '.join(regeln)}. Falls eine davon bisher Vermutung ist, "
            f"kannst du sie jetzt im Wissens-Repo auf verifiziert heben (C5 — Stufenwechsel "
            f"macht der Mensch, nicht der Server) und diesen Block als Beleg eintragen.")
    return " ".join(meldung)


def suche_bloecke(bloecke: list[Block], suchbegriff: str) -> list[Block]:
    s = suchbegriff.lower()
    return [b for b in bloecke
            if s in b.kernbauteil.lower() or s in b.titel.lower() or s in b.topologie.lower()]


def block_volltext(b: Block) -> str:
    zeilen = [
        f"### {b.id} — {b.titel}",
        f"Kernbauteil: {b.kernbauteil} | Projekt: {b.projekt} | Datum: {b.datum} | Revision: {b.revision}",
        f"Topologie: {b.topologie}",
        f"Gebaut: {b.gebaut}",
        f"Gemessen: {b.gemessen}",
        f"Messbedingungen: {b.messbedingungen}",
        f"Getestete Grenzen: {b.grenzen}",
    ]
    if b.gescheitert:
        zeilen.append(f"Gescheitert: {b.gescheitert}")
    if b.fallback:
        zeilen.append(f"Fallback: {b.fallback}")
    if b.regeln:
        zeilen.append(f"Verknüpfte Regeln: {', '.join(b.regeln)}")
    zeilen.append(f"Eingefrorener Ausschnitt: bloecke/{b.ausschnitt_datei}")
    zeilen.append(
        "⚠ D4: verifiziert gilt exakt für diesen Aufbau innerhalb der getesteten Grenzen. "
        "Jede Übertragung auf einen ähnlichen Fall ist eine Vermutung — Abweichungen "
        "(Bauteile, Werte, Layout, Last) als Differenzliste explizit aufzählen.")
    return "\n".join(zeilen)
