"""Netz-Ableitung: reine Funktion, getestet mit einem Mini-ESP32-Design."""
from types import SimpleNamespace as NS

import pytest

from app.kicad.library import load_library
from app.kicad.netlist import build_export_model, normalize_power_net


def test_power_label_normalization():
    assert normalize_power_net("3.3V") == "3V3"
    assert normalize_power_net("VBUS 5V") == "VBUS"
    assert normalize_power_net("VBAT 3.6-4.2V") == "VBAT"
    assert normalize_power_net("12V") == "12V"


@pytest.fixture()
def minimal_design():
    blocks = [
        NS(id="b-mcu", name="MCU"),
        NS(id="b-sens", name="Sensor"),
        NS(id="b-reg", name="Regler"),
    ]
    connections = [
        NS(source_block_id="b-mcu", target_block_id="b-sens", label="SDA/SCL", conn_type="i2c"),
        NS(source_block_id="b-reg", target_block_id="b-mcu", label="3.3V", conn_type="power"),
        NS(source_block_id="b-reg", target_block_id="b-sens", label="3.3V", conn_type="power"),
        NS(source_block_id="b-mcu", target_block_id="b-sens", label="GND", conn_type="gnd"),
        NS(source_block_id="b-reg", target_block_id="b-mcu", label="GND", conn_type="gnd"),
    ]
    components = [
        NS(id="c1", block_id="b-mcu", name="ESP32-S3-WROOM-1-N8", type="mcu",
           mpn="ESP32-S3-WROOM-1-N8", value=None, net_role=None),
        NS(id="c2", block_id="b-sens", name="SHT31-DIS-B", type="sensor",
           mpn="SHT31-DIS-B", value=None, net_role=None),
        NS(id="c3", block_id="b-sens", name="10kΩ Widerstand", type="passive_resistor",
           mpn="RC0402FR-0710KL", value="10kΩ", net_role="pullup:SDA"),
        NS(id="c4", block_id="b-mcu", name="100nF Kondensator", type="passive_capacitor",
           mpn="GCM155R71C104KA55D", value="100nF", net_role="decoupling"),
        NS(id="c5", block_id="b-mcu", name="Exotisches Teil", type="exotic_ic",
           mpn="GIBTSNICHT-1", value=None, net_role=None),
    ]
    return blocks, connections, components


def _by_ref(model, ref):
    return next(i for i in model.instances if i.ref == ref)


def test_i2c_connection_creates_sda_scl_nets(minimal_design):
    model = build_export_model(*minimal_design, load_library())
    mcu = _by_ref(model, "U1")
    # ESP32: SDA=Pin 12, SCL=Pin 17, VDD=Pin 2 → 3V3, GND=1/40/41
    assert mcu.pin_nets["12"] == "SDA"
    assert mcu.pin_nets["17"] == "SCL"
    assert mcu.pin_nets["2"] == "3V3"
    assert mcu.pin_nets["1"] == "GND"
    sensor = _by_ref(model, "U2")
    assert sensor.pin_nets["1"] == "SDA"   # SHT31 SDA
    assert sensor.pin_nets["4"] == "SCL"
    assert sensor.pin_nets["5"] == "3V3"


def test_pullup_resistor_nets(minimal_design):
    model = build_export_model(*minimal_design, load_library())
    r1 = _by_ref(model, "R1")
    assert set(r1.pin_nets.values()) == {"SDA", "3V3"}
    assert r1.status == "fallback"  # MPN nicht in Bibliothek → Device:R


def test_decoupling_cap_gets_block_supply_and_gnd(minimal_design):
    model = build_export_model(*minimal_design, load_library())
    c1 = _by_ref(model, "C1")
    assert set(c1.pin_nets.values()) == {"3V3", "GND"}


def test_unknown_component_lands_in_unmapped(minimal_design):
    model = build_export_model(*minimal_design, load_library())
    assert len(model.unmapped) == 1
    assert model.unmapped[0]["mpn"] == "GIBTSNICHT-1"
    assert model.unmapped[0]["reason"] == "kein Bibliothekseintrag"


def test_refs_are_deterministic(minimal_design):
    lib = load_library()
    a = build_export_model(*minimal_design, lib)
    b = build_export_model(*minimal_design, lib)
    assert [i.ref for i in a.instances] == [i.ref for i in b.instances]
    assert [i.pin_nets for i in a.instances] == [i.pin_nets for i in b.instances]
