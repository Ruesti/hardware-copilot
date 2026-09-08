"""Dienst-Schicht der Wissensschicht: die Logik hinter den MCP-Tools.

Rein lesend gegenüber der Regelbasis (§0 Phase 2); einzige Schreiboperation ist
das Lücken-Protokoll (C6). Regeln werden pro Aufruf frisch geladen — bei der
Repo-Größe billig und nie veraltet.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from .checker import UnbekannteRegel, check_hint
from .format import kurzform, volltext
from .gaps import list_gaps, report_gap
from .matching import Treffer, match_rules
from .store import load_rules


class WissensDienst:
    def __init__(self, repo_pfad: Path):
        self.repo = Path(repo_pfad)
        self.luecken_datei = self.repo / "luecken.md"

    def _regeln(self):
        return load_rules(self.repo)

    def query(self, klassen: list[str], achsen: dict | None = None,
              frage: str | None = None) -> str:
        fall = {"klasse": klassen, **(achsen or {})}
        treffer = match_rules(self._regeln(), fall)
        if not treffer:
            beschreibung = frage or f"klasse={','.join(klassen)}"
            text = f"Keine belegte Regel zu {beschreibung} vorhanden."
            if frage:
                report_gap(self.luecken_datei, frage=frage,
                           grund="keine Regel in der Regelbasis", datum=str(date.today()))
                text += " Die Frage wurde im Lücken-Protokoll vermerkt (Kandidat für eine neue Regel mit Quelle)."
            return text
        zeilen = [kurzform(t.regel) for t in treffer]
        zeilen.append("")
        zeilen.append("Details je Regel über get_rule(<ID>) — Begründung, Quelle mit Fundstelle, Ausnahmen.")
        unbestaetigt = [t for t in treffer if t.unbestaetigt]
        for t in unbestaetigt:
            zeilen.append(f"⚠ {t.regel.id}: Bedingungen im Fall nicht angegeben, "
                          f"daher unbestätigt: {', '.join(t.unbestaetigt)}")
        return "\n".join(zeilen)

    def regel(self, regel_id: str) -> str:
        regeln = {r.id: r for r in self._regeln()}
        if regel_id not in regeln:
            return f"Regel {regel_id} existiert nicht in der Regelbasis."
        return volltext(Treffer(regel=regeln[regel_id]))

    def pruefe(self, regel_id: str, regel_stufe: str, anwendung_stufe: str) -> str:
        regeln = {r.id: r for r in self._regeln()}
        try:
            e = check_hint(regeln, regel_id, regel_stufe=regel_stufe,
                           anwendung_stufe=anwendung_stufe)
        except UnbekannteRegel as exc:
            return str(exc)
        zeilen = [f"Regel-Teil: {e.regel_stufe} | Anwendungs-Teil: {e.anwendung_stufe}"]
        zeilen += e.korrekturen
        return "\n".join(zeilen)

    def luecken(self) -> list[dict]:
        return list_gaps(self.luecken_datei)

    def melde_luecke(self, frage: str, grund: str) -> str:
        report_gap(self.luecken_datei, frage=frage, grund=grund, datum=str(date.today()))
        return f"Lücke vermerkt: {frage}"
