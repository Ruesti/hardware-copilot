"""F3-Ausgabeformat: lesbarer Markdown-Block mit festen Zeilen, darunter Rohdaten als JSON.

Das Modell soll den Markdown-Teil unverändert durchreichen (§0 F3); Vermutungen
tragen den C4-Pflichtmarker, damit sie beim Überfliegen nicht wie belegt wirken.
"""
from __future__ import annotations

import json
from dataclasses import asdict

from .matching import Treffer
from .store import Regel


def _stufen_label(regel: Regel) -> str:
    if regel.stufe == "vermutung":
        return "⚠ VERMUTUNG"
    return regel.stufe.upper()


def _quellen_zeile(regel: Regel) -> str:
    q = regel.quelle
    if q["typ"] == "keine":
        return "Quelle: keine"
    kennung = f" ({q['dokument']})" if q.get("dokument") else ""
    return f"Quelle: {q['titel']}{kennung}, {q['fundstelle']}"


def kurzform(regel: Regel) -> str:
    """F4-Kurzform: ID, Aussage, Stufe — Details erst per Nachfass-Tool."""
    return f"[{regel.id}] {_stufen_label(regel)} ({regel.staerke}): {regel.aussage}"


def volltext(treffer: Treffer) -> str:
    """F3-Volltext eines Treffers: Markdown + eingebetteter JSON-Block."""
    r = treffer.regel
    zeilen = [
        f"### {r.id} — {r.bereich}",
        f"**Stufe: {_stufen_label(r)}** | Stärke: {r.staerke}",
        r.aussage,
        f"Begründung: {r.begruendung}",
        _quellen_zeile(r),
    ]
    if r.quelle.get("zitat"):
        zeilen.append(f'> "{r.quelle["zitat"]}"')
    geltung = ", ".join(f"{k}={v}" for k, v in r.geltung.items())
    zeilen.append(f"Geltung: {geltung}")
    if r.ausnahmen:
        zeilen.append("Ausnahmen: " + "; ".join(r.ausnahmen))
    if treffer.unbestaetigt:
        zeilen.append("⚠ Unbestätigte Bedingungen (im Fall nicht angegeben): "
                      + ", ".join(treffer.unbestaetigt))
    daten = {"regel": asdict(r), "unbestaetigt": treffer.unbestaetigt}
    zeilen.append("```json\n" + json.dumps(daten, ensure_ascii=False) + "\n```")
    return "\n".join(zeilen)
