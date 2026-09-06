from app.kicad import sexpr
from app.kicad.symbols import extract_symbol, symbol_pins

from .conftest import KICAD_SYMBOLS, requires_kicad


def test_sexpr_roundtrip():
    node = sexpr.parse('(a (b "c d") 1.5)')
    assert node == ["a", ["b", sexpr.Quoted("c d")], "1.5"]
    assert sexpr.dumps(node).split() == '(a (b "c d") 1.5)'.split()


def test_sexpr_quoted_escaping():
    node = sexpr.parse('(x "a \\"b\\" c")')
    assert node[1] == 'a "b" c'
    assert '\\"b\\"' in sexpr.dumps(node)


@requires_kicad
def test_extract_device_r_has_two_pins():
    node = extract_symbol("Device", "R", KICAD_SYMBOLS)
    assert str(node[1]) == "Device:R"
    pins = symbol_pins(node)
    assert sorted(p.number for p in pins) == ["1", "2"]


@requires_kicad
def test_extract_resolves_extends():
    # Diode:ESD5Zxx erbt via extends von ZPYxx — Extraktion muss Pins liefern
    node = extract_symbol("Diode", "ESD5Zxx", KICAD_SYMBOLS)
    pins = symbol_pins(node)
    assert sorted(p.number for p in pins) == ["1", "2"]
    text = sexpr.dumps(node)
    assert "extends" not in text  # Merge hat extends ersetzt
    assert "ZPYxx" not in text    # Untersymbole auf Kind-Namen umbenannt


@requires_kicad
def test_extract_unknown_symbol_raises():
    import pytest
    with pytest.raises(KeyError):
        extract_symbol("Device", "GibtEsNicht", KICAD_SYMBOLS)
