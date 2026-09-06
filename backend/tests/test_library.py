from app.kicad.library import load_library


def test_load_library_has_mcp73831():
    lib = load_library()
    part = lib.for_component("MCP73831T-2ACI/OT", "power_ic")
    assert part is not None
    assert part.lib_id == "Battery_Management:MCP73831-2-OT"
    assert part.role_to_pin["VBAT"] == ["3"]  # Datenblatt DS20001984H, Package Types
    assert part.role_to_pin["VDD"] == ["4"]
    assert part.validated is True


def test_type_fallback_resistor():
    lib = load_library()
    part = lib.for_component("RC0402FR-0710KL-UNBEKANNT", "passive_resistor")
    assert part.lib_id == "Device:R"
    assert part.role_to_pin == {"P1": ["1"], "P2": ["2"]}
    assert lib.is_fallback("RC0402FR-0710KL-UNBEKANNT")


def test_unknown_component_returns_none():
    lib = load_library()
    assert lib.for_component("GIBTSNICHT-123", "exotic_ic") is None


def test_all_eight_mpn_entries_present():
    lib = load_library()
    expected = {
        "ESP32-S3-WROOM-1-N8", "SHT31-DIS-B", "MCP73831T-2ACI/OT",
        "XC6220A331MR-G", "USB4135-GF-A", "DM3AT-SF-PEJM5",
        "S2B-PH-K-S", "ESD5Z5.0T1G",
    }
    assert expected <= set(lib.parts)
    for part in lib.parts.values():
        assert part.validated, f"{part.lib_id}: MPN-Einträge müssen geprüft (validated) sein"
