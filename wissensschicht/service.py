"""Dienst-Schicht der Wissensschicht: die Logik hinter den MCP-Tools.

Rein lesend gegenüber der Regelbasis (§0 Phase 2); Schreiboperationen sind das
Lücken-Protokoll (C6) und — seit Phase 4 — das Erfassen von Verified Blocks.
Regeln werden pro Aufruf frisch geladen — bei der Repo-Größe billig und nie
veraltet. Heikle Bereiche (§0 Block E) stellen eine Frage statt einer Anweisung.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from .blocks import BlockFehler, block_volltext, erfasse_block, lade_bloecke, suche_bloecke
from .checker import UnbekannteRegel, check_hint
from .format import kurzform, volltext
from .gaps import list_gaps, report_gap
from .heikel import lade_heikel, pruefe_heikel
from .matching import Treffer, match_rules
from .store import load_rules

# Numerische Fall-Achsen: speisen die Heikel-Schwellen (E2), sind keine Regel-Achsen.
NUMERISCHE_FALL_ACHSEN = {"spannung_v", "strom_a"}


class WissensDienst:
    def __init__(self, repo_pfad: Path):
        self.repo = Path(repo_pfad)
        self.luecken_datei = self.repo / "luecken.md"

    def _regeln(self):
        return load_rules(self.repo)

    def _validiere_fall(self, regeln, klassen: list[str], achsen: dict):
        """Katalog-Validierung (GRENZEN.md Punkt 5): nichts still schlucken."""
        bekannte_klassen = sorted({r.geltung["klasse"] for r in regeln})
        unbekannte_klassen = [k for k in klassen if k not in bekannte_klassen]
        bekannte_werte: dict[str, set] = {}
        for r in regeln:
            for a, w in r.geltung.items():
                if a != "klasse":
                    bekannte_werte.setdefault(a, set()).add(w)
        warnungen = []
        for a, w in achsen.items():
            if a in NUMERISCHE_FALL_ACHSEN:
                continue
            if a not in bekannte_werte:
                warnungen.append(f"Achtung: Achse {a} ist in keiner Regel bekannt — Wert wird nicht geprüft.")
            elif w not in bekannte_werte[a]:
                warnungen.append(f"Achtung: {a}={w} ist ein unbekannter Wert "
                                 f"(bekannt: {', '.join(sorted(map(str, bekannte_werte[a])))}).")
        return bekannte_klassen, unbekannte_klassen, warnungen

    def query(self, klassen: list[str], achsen: dict | None = None,
              frage: str | None = None) -> str:
        achsen = achsen or {}
        fall = {"klasse": klassen, **achsen}
        regeln = self._regeln()
        bekannte_klassen, unbekannte_klassen, warnungen = self._validiere_fall(regeln, klassen, achsen)

        if unbekannte_klassen and len(unbekannte_klassen) == len(klassen):
            return (f"Unbekannte Klasse(n): {', '.join(unbekannte_klassen)}. "
                    f"Bekannte Klassen: {', '.join(bekannte_klassen)}. "
                    "Bitte mit einer bekannten Klasse erneut abfragen (Achsenkatalog: SCHEMA.md im Wissens-Repo).")

        zeilen: list[str] = []
        if unbekannte_klassen:
            zeilen.append(f"Achtung: unbekannte Klasse(n) ignoriert: {', '.join(unbekannte_klassen)} "
                          f"(bekannt: {', '.join(bekannte_klassen)}).")
        zeilen.extend(warnungen)

        # Block E: Frage statt Anweisung (vor allem anderen).
        heikel_treffer = pruefe_heikel(lade_heikel(self.repo), fall)
        for b in heikel_treffer:
            zeilen.append(f"⚠ HEIKLER BEREICH ({b.name}) — Frage statt Anweisung (§0 Block E):")
            zeilen.append(b.frage)
            if b.fundstelle:
                zeilen.append(f"Nachlesen: {b.fundstelle}")
            if b.fundstelle_hinweis:
                zeilen.append(f"Hinweis: {b.fundstelle_hinweis}")
            zeilen.append("")

        unterdrueckt = [b for b in heikel_treffer if b.unterdrueckt_regeln]
        if unterdrueckt:
            for b in unterdrueckt:
                if b.regel_unterdrueckung_grund:
                    zeilen.append(b.regel_unterdrueckung_grund)
            return "\n".join(zeilen)

        treffer = match_rules(regeln, fall)
        if not treffer:
            beschreibung = frage or f"klasse={','.join(klassen)}" + (
                f", {', '.join(f'{a}={w}' for a, w in achsen.items())}" if achsen else "")
            zeilen.append(f"Keine belegte Regel zu {beschreibung} vorhanden.")
            report_gap(self.luecken_datei, frage=beschreibung,
                       grund="keine Regel in der Regelbasis", datum=str(date.today()))
            zeilen.append("Die Frage wurde im Lücken-Protokoll vermerkt (Kandidat für eine neue Regel mit Quelle).")
            return "\n".join(zeilen)

        zeilen.extend(kurzform(t.regel) for t in treffer)
        zeilen.append("")
        zeilen.append("Details je Regel über get_rule(<ID>) — Begründung, Quelle mit Fundstelle, Ausnahmen.")
        for t in treffer:
            if t.unbestaetigt:
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

    def erfasse_block(self, **daten) -> str:
        try:
            return erfasse_block(self.repo, **daten)
        except BlockFehler as e:
            return str(e)

    def bloecke_suchen(self, suchbegriff: str) -> str:
        treffer = suche_bloecke(lade_bloecke(self.repo), suchbegriff)
        if not treffer:
            return (f"Kein Verified Block zu '{suchbegriff}'. Es zählt nur, was real "
                    "aufgebaut und vermessen wurde — Regeln liefert query_rules.")
        zeilen = [f"[{b.id}] {b.titel} — {b.kernbauteil}, {b.projekt}, {b.datum} "
                  f"(Grenzen: {b.grenzen})" for b in treffer]
        zeilen.append("")
        zeilen.append("Volltext über get_block(<ID>). ⚠ D4: Übertragung auf einen ähnlichen, "
                      "nicht identischen Fall ist Vermutung — Abweichungen explizit auflisten.")
        return "\n".join(zeilen)

    def block(self, block_id: str) -> str:
        bloecke = {b.id: b for b in lade_bloecke(self.repo)}
        if block_id not in bloecke:
            return f"Block {block_id} existiert nicht."
        return block_volltext(bloecke[block_id])

    def luecken(self) -> list[dict]:
        return list_gaps(self.luecken_datei)

    def melde_luecke(self, frage: str, grund: str) -> str:
        report_gap(self.luecken_datei, frage=frage, grund=grund, datum=str(date.today()))
        return f"Lücke vermerkt: {frage}"
