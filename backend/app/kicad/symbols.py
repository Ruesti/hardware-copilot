"""Extrahiert Symboldefinitionen aus den offiziellen KiCad-Bibliotheken.

Formatregeln (per ERC-Bisektion verifiziert, siehe Format-Spike):
- Im Schaltplan trägt nur der Symbolkopf den Namen "<Lib>:<Symbol>";
  Unit-Untersymbole behalten den nackten Namen ("R_0_1").
- extends-Symbole werden aufgelöst: Grafik/Pins des Parents, Properties des
  Kinds; Untersymbole werden auf den Kind-Namen umbenannt.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from . import sexpr
from .sexpr import Quoted


@dataclass(frozen=True)
class Pin:
    number: str
    name: str
    x: float
    y: float
    rotation: int


@lru_cache(maxsize=64)
def _load_lib(path_str: str) -> dict[str, list]:
    doc = sexpr.parse(Path(path_str).read_text())
    out: dict[str, list] = {}
    for node in doc[1:]:
        if isinstance(node, list) and node and node[0] == "symbol":
            out[str(node[1])] = node
    return out


def extract_symbol(lib_name: str, symbol_name: str, symbols_dir: Path) -> list:
    lib = _load_lib(str(symbols_dir / f"{lib_name}.kicad_sym"))
    if symbol_name not in lib:
        raise KeyError(f"Symbol {symbol_name!r} nicht in Bibliothek {lib_name!r}")
    node = _deep_copy(lib[symbol_name])
    parent_name = _extends_target(node)
    if parent_name:
        parent = _deep_copy(lib[parent_name])
        node = _merge_extends(parent, node)
        _rename_subsymbols(node, parent_name, symbol_name)
    node[1] = Quoted(f"{lib_name}:{symbol_name}")
    return node


def _extends_target(node: list) -> str | None:
    for child in node:
        if isinstance(child, list) and child and child[0] == "extends":
            return str(child[1])
    return None


def _merge_extends(parent: list, child: list) -> list:
    """Parent-Body + Properties des Kinds (Kind-Properties gewinnen)."""
    child_props = {
        str(c[1]): c
        for c in child
        if isinstance(c, list) and c and c[0] == "property"
    }
    merged: list = []
    for c in parent:
        if isinstance(c, list) and c and c[0] == "property" and str(c[1]) in child_props:
            merged.append(child_props.pop(str(c[1])))
        else:
            merged.append(c)
    insert_at = 2
    for prop in child_props.values():
        merged.insert(insert_at, prop)
    return merged


def _rename_subsymbols(node: list, old_name: str, new_name: str) -> None:
    for child in node:
        if isinstance(child, list) and child and child[0] == "symbol":
            child[1] = Quoted(str(child[1]).replace(old_name, new_name, 1))


def _deep_copy(node):
    return [(_deep_copy(c) if isinstance(c, list) else c) for c in node]


def symbol_pins(node: list) -> list[Pin]:
    pins: list[Pin] = []

    def walk(n: list) -> None:
        for child in n:
            if isinstance(child, list) and child:
                if child[0] == "pin":
                    at = next((c for c in child if isinstance(c, list) and c and c[0] == "at"), None)
                    name = next((c for c in child if isinstance(c, list) and c and c[0] == "name"), None)
                    number = next((c for c in child if isinstance(c, list) and c and c[0] == "number"), None)
                    if at is None or name is None or number is None:
                        continue
                    pins.append(Pin(
                        number=str(number[1]),
                        name=str(name[1]),
                        x=float(at[1]),
                        y=float(at[2]),
                        rotation=int(float(at[3])) if len(at) > 3 else 0,
                    ))
                else:
                    walk(child)

    walk(node)
    return pins
