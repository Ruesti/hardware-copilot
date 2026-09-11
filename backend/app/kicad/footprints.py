"""Automatische Footprint-Zuordnung aus dem Gehäuse-Feld der Komponenten.

Deterministisch: Gehäusenamen werden normalisiert und gegen eine kuratierte
Tabelle aufgelöst; jeder Tabellenwert wird per Test gegen die installierte
KiCad-Footprint-Bibliothek geprüft. Kein Treffer → leerer Footprint (ehrlich
offen statt geraten), sichtbar im Export-Report.
"""
from __future__ import annotations

import re

# Chip-Gehäuse (imperial) → KiCad-Namenszusatz
_CHIP_SIZES = {
    "0201": "0201_0603Metric",
    "0402": "0402_1005Metric",
    "0603": "0603_1608Metric",
    "0805": "0805_2012Metric",
    "1206": "1206_3216Metric",
    "1210": "1210_3225Metric",
}

# Typklasse → (Bibliothek, Präfix) für Chip-Gehäuse
_CHIP_LIBS = {
    "passive_resistor": ("Resistor_SMD", "R"),
    "passive_capacitor": ("Capacitor_SMD", "C"),
    "passive_inductor": ("Inductor_SMD", "L"),
    "diode": ("Diode_SMD", "D"),
    "protection": ("Diode_SMD", "D"),
}

# Typunabhängige Gehäuse (normalisierter Name → vollständiger Footprint)
_PACKAGES = {
    "SOT-23": "Package_TO_SOT_SMD:SOT-23",
    "SOT-23-3": "Package_TO_SOT_SMD:SOT-23",
    "SOT-23-5": "Package_TO_SOT_SMD:SOT-23-5",
    "SOT-25": "Package_TO_SOT_SMD:SOT-23-5",   # gebräuchliches Synonym
    "SOT-23-6": "Package_TO_SOT_SMD:SOT-23-6",
    "SOT-26": "Package_TO_SOT_SMD:SOT-23-6",   # gebräuchliches Synonym
    "SOT-89": "Package_TO_SOT_SMD:SOT-89-3",
    "SOT-223": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "SOT-323": "Package_TO_SOT_SMD:SOT-323_SC-70",
    "SC-70": "Package_TO_SOT_SMD:SOT-323_SC-70",
    "SOD-123": "Diode_SMD:D_SOD-123",
    "SOD-123F": "Diode_SMD:D_SOD-123F",
    "SOD-323": "Diode_SMD:D_SOD-323",
    "SOD-523": "Diode_SMD:D_SOD-523",
    "SOD-923": "Diode_SMD:D_SOD-923",
    "SMA": "Diode_SMD:D_SMA",
    "SMB": "Diode_SMD:D_SMB",
    "SMC": "Diode_SMD:D_SMC",
    "DO-214AC": "Diode_SMD:D_SMA",
    "DO-214AA": "Diode_SMD:D_SMB",
    "DO-214AB": "Diode_SMD:D_SMC",
    "SOIC-8": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "SOIC-14": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "SOIC-16": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
}


def _normalize(package: str) -> str:
    """'sot23-5', 'SOT 23-5 (SC-74A)', 'SOD523' → 'SOT-23-5' / 'SOD-523'."""
    p = package.strip().upper()
    p = re.sub(r"\(.*?\)", "", p)                 # Klammerzusätze weg
    p = re.sub(r"\b(SMD|THT|PACKAGE)\b", "", p)   # Fülltokens weg
    p = p.strip(" ,;")
    p = re.sub(r"\s+", "-", p)
    p = re.sub(r"^(SOT|SOD|SC)(\d)", r"\1-\2", p)  # SOT23 → SOT-23
    p = re.sub(r"-{2,}", "-", p).strip("-")
    return p


# Bedrahtete Standard-Footprints je Typklasse (mount="tht")
_THT_BY_TYPE = {
    "passive_resistor": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "passive_capacitor": "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
    "diode": "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",
    "protection": "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",
}


def guess_footprint(comp_type: str | None, package: str | None,
                    mount: str = "smd") -> str:
    """Bester deterministischer Footprint für (Typ, Gehäuse); '' wenn unklar.

    mount="tht": Passive/Dioden bekommen bedrahtete Standard-Footprints
    (Handlöt-/Prototypen-Bestückung), unabhängig vom SMD-Gehäuse im
    package-Feld. ICs/Module folgen weiterhin der Bibliothek."""
    if mount == "tht":
        tht = _THT_BY_TYPE.get(comp_type or "")
        if tht:
            return tht
    if not package:
        return ""
    if ":" in package:            # bereits ein vollständiger KiCad-Footprint
        return package
    norm = _normalize(package)
    if not norm:
        return ""
    if norm in _CHIP_SIZES:
        lib_prefix = _CHIP_LIBS.get(comp_type or "")
        if lib_prefix:
            lib, prefix = lib_prefix
            return f"{lib}:{prefix}_{_CHIP_SIZES[norm]}"
        return ""
    return _PACKAGES.get(norm, "")
