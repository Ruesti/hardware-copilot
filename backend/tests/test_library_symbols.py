"""Sicherheitsnetz: jede Pin-Angabe der Bibliothek existiert im echten Symbol."""
from app.kicad.library import load_library
from app.kicad.symbols import extract_symbol, symbol_pins

from .conftest import KICAD_SYMBOLS, requires_kicad


@requires_kicad
def test_every_library_pin_exists_in_symbol():
    lib = load_library()
    all_parts = list(lib.parts.items()) + list(lib.type_fallbacks.items())
    assert all_parts
    for key, part in all_parts:
        libname, symname = part.lib_id.split(":", 1)
        pins = {p.number for p in symbol_pins(extract_symbol(libname, symname, KICAD_SYMBOLS))}
        for role, numbers in part.role_to_pin.items():
            for n in numbers:
                assert n in pins, (
                    f"{key}: Rolle {role} nennt Pin {n}, "
                    f"Symbol {part.lib_id} hat nur {sorted(pins)}"
                )
