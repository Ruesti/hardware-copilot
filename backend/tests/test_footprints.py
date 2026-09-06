"""Automatische Footprint-Zuordnung: Normalisierung, Mapping, Existenz."""
from pathlib import Path

from app.kicad.footprints import _CHIP_LIBS, _CHIP_SIZES, _PACKAGES, guess_footprint

from .conftest import requires_kicad

FOOTPRINTS_DIR = Path("/usr/share/kicad/footprints")


def test_chip_packages():
    assert guess_footprint("passive_resistor", "0402") == "Resistor_SMD:R_0402_1005Metric"
    assert guess_footprint("passive_capacitor", "0805") == "Capacitor_SMD:C_0805_2012Metric"
    assert guess_footprint("protection", "0603") == "Diode_SMD:D_0603_1608Metric"
    # Chip-Größe ohne bekannte Typklasse → kein Raten
    assert guess_footprint("connector", "0402") == ""


def test_normalization_variants():
    assert guess_footprint("power_ic", "SOT-23-5") == "Package_TO_SOT_SMD:SOT-23-5"
    assert guess_footprint("power_ic", "sot23-5") == "Package_TO_SOT_SMD:SOT-23-5"
    assert guess_footprint("power_ic", "SOT 23-5 (SC-74A)") == "Package_TO_SOT_SMD:SOT-23-5"
    assert guess_footprint("power_ic", "SOT-25") == "Package_TO_SOT_SMD:SOT-23-5"
    assert guess_footprint("protection", "SOD523") == "Diode_SMD:D_SOD-523"
    assert guess_footprint("diode", "SOD-123F SMD") == "Diode_SMD:D_SOD-123F"


def test_passthrough_and_unknown():
    # Vollständige KiCad-Footprints werden durchgereicht
    assert guess_footprint("mcu", "RF_Module:ESP32-S3-WROOM-1") == "RF_Module:ESP32-S3-WROOM-1"
    # Unbekanntes bleibt ehrlich leer
    assert guess_footprint("connector", "SMD Module") == ""
    assert guess_footprint("mcu", "") == ""
    assert guess_footprint("mcu", None) == ""


@requires_kicad
def test_every_mapped_footprint_exists():
    """Jeder Footprint, den die Tabellen erzeugen können, existiert wirklich."""
    candidates = set(_PACKAGES.values())
    for lib, prefix in _CHIP_LIBS.values():
        for suffix in _CHIP_SIZES.values():
            candidates.add(f"{lib}:{prefix}_{suffix}")
    for fp in sorted(candidates):
        libname, fpname = fp.split(":", 1)
        path = FOOTPRINTS_DIR / f"{libname}.pretty" / f"{fpname}.kicad_mod"
        assert path.exists(), f"Tabellen-Footprint existiert nicht: {fp}"


def test_tht_mount():
    assert guess_footprint("passive_resistor", "0402", mount="tht") \
        == "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
    assert guess_footprint("passive_capacitor", "0805", mount="tht") \
        == "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
    # ICs bleiben bei THT unangetastet (kein bedrahtetes Pendant unterstellt)
    assert guess_footprint("power_ic", "SOT-23-5", mount="tht") \
        == "Package_TO_SOT_SMD:SOT-23-5"


@requires_kicad
def test_tht_footprints_exist():
    from app.kicad.footprints import _THT_BY_TYPE
    for fp in set(_THT_BY_TYPE.values()):
        libname, fpname = fp.split(":", 1)
        path = FOOTPRINTS_DIR / f"{libname}.pretty" / f"{fpname}.kicad_mod"
        assert path.exists(), f"THT-Footprint existiert nicht: {fp}"
