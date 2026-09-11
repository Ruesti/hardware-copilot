"""Modell-Bauer: Projekt-Positionen → ExportModel (Kaskade, Report, Warnungen)."""
from backend.app.kicad.library import Library, LibraryPart
from backend.app.kicad.modell import baue_export_modell


def projekt(positionen):
    return {"id": 1, "name": "Blink-Board", "status": "offen", "positionen": positionen}


def pos(**kw):
    basis = {"referenz": "C1", "bezeichnung": "100nF", "menge": 1, "klasse": "",
             "baugruppe": "", "pins": None, "kicad_symbol": "", "kicad_footprint": "",
             "notiz": "", "teil_id": None, "bestand": None, "preis": None,
             "alle_preise": [], "id": 1}
    basis.update(kw)
    return basis


LEER = Library()
MIT_MCP = Library(parts={"MCP73831T-2ACI/OT": LibraryPart(
    lib_id="Battery_Management:MCP73831-2-OT",
    footprint="Package_TO_SOT_SMD:SOT-23-5", role_to_pin={})})


def test_explizites_symbol_gewinnt():
    m = baue_export_modell(projekt([pos(kicad_symbol="Device:C",
                                        pins={"1": "GND", "2": "+3V3"},
                                        baugruppe="Versorgung")]), LEER)

    inst = m.instances[0]
    assert inst.lib_id == "Device:C" and inst.status == "mapped"
    assert inst.block_name == "Versorgung"
    assert inst.pin_nets == {"1": "GND", "2": "+3V3"}
    assert m.unmapped == []


def test_bibliothek_per_herstellernummer():
    p = pos(referenz="U1", bezeichnung="MCP73831",
            bestand={"menge": 3, "fach": "B/1", "hersteller_nr": "MCP73831T-2ACI/OT"})

    m = baue_export_modell(projekt([p]), MIT_MCP)

    assert m.instances[0].lib_id == "Battery_Management:MCP73831-2-OT"
    assert m.instances[0].footprint == "Package_TO_SOT_SMD:SOT-23-5"


def test_ohne_zuordnung_landet_im_report():
    m = baue_export_modell(projekt([pos(referenz="R7", bezeichnung="10k")]), LEER)

    assert m.instances == []
    assert m.unmapped[0]["referenz"] == "R7"
    assert "kicad_symbol" in m.unmapped[0]["grund"]


def test_warnungen_menge_und_pins():
    m = baue_export_modell(projekt([
        pos(referenz="C1", kicad_symbol="Device:C", menge=2),
    ]), LEER)

    assert any("Menge 2" in w for w in m.warnings)
    assert any("keine Pin-Netze" in w for w in m.warnings)


def test_leere_baugruppe_wird_sonstiges():
    m = baue_export_modell(projekt([pos(kicad_symbol="Device:C")]), LEER)

    assert m.instances[0].block_name == "Sonstiges"
