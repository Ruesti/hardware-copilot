"""F3-Ausgabeformat: Markdown mit eingebettetem JSON, C4-Marker für Vermutungen, F4-Kurzform."""
import json
import re

from wissensschicht.format import kurzform, volltext
from wissensschicht.matching import Treffer
from .test_matching import regel


def test_kurzform_enthaelt_id_aussage_stufe():
    zeile = kurzform(regel("R-005", "schaltregler"))

    assert "R-005" in zeile
    assert "Aussage R-005" in zeile
    assert "BELEGT" in zeile


def test_kurzform_vermutung_traegt_warnmarker():
    zeile = kurzform(regel("R-008", "schaltregler", stufe="vermutung"))

    assert "⚠ VERMUTUNG" in zeile


def test_volltext_belegt_enthaelt_begruendung_quelle_und_zitat():
    text = volltext(Treffer(regel=regel("R-005", "schaltregler")))

    assert "Stufe: BELEGT" in text
    assert "B" in text          # Begründung
    assert "T" in text          # Quellen-Titel
    assert "S. 1" in text       # Fundstelle
    assert "Z" in text          # Zitat


def test_volltext_vermutung_hat_marker_und_quelle_keine():
    text = volltext(Treffer(regel=regel("R-008", "schaltregler", stufe="vermutung")))

    assert "⚠ VERMUTUNG" in text
    assert "Quelle: keine" in text


def test_volltext_meldet_unbestaetigte_bedingungen():
    t = Treffer(regel=regel("R-009", "mcu_wifi", antenne="pcb_onboard"),
                unbestaetigt=["antenne=pcb_onboard"])

    text = volltext(t)

    assert "antenne=pcb_onboard" in text
    assert "unbestätigt" in text.lower()


def test_volltext_endet_mit_parsebarem_json_block():
    text = volltext(Treffer(regel=regel("R-005", "schaltregler")))

    m = re.search(r"```json\n(.*?)\n```", text, re.S)
    assert m, "JSON-Block fehlt"
    daten = json.loads(m.group(1))
    assert daten["regel"]["id"] == "R-005"
    assert daten["regel"]["stufe"] == "belegt"
