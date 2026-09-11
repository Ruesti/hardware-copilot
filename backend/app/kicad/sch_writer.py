"""Erzeugt eine self-contained .kicad_sch (KiCad 9) aus dem Export-Modell.

Formatvorlage ist die per ERC verifizierte Fixture aus dem Format-Spike:
Version 20250114, lokale Labels, lib-Präfix nur am Symbolkopf, deterministische
UUIDs (uuid5 über Referenz-IDs), 1,27-mm-Raster.

ERC-Regeln, die der Writer aktiv bedient:
- Netze mit nur einem Anschlusspunkt bekommen kein Label (wäre "dangling"),
  sondern ein no_connect + Warnung im Modell.
- Versorgungsnetze, die an power_in-Pins hängen, aber von keinem power_out-Pin
  getrieben werden (GND/VBUS von Steckverbindern), bekommen ein PWR_FLAG.
"""
from __future__ import annotations

import math
import uuid
from collections import Counter
from pathlib import Path

from . import sexpr
from .modell import ExportModel, SymbolInstance
from .symbols import Pin, extract_symbol, symbol_pins

EXPORT_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
GRID = 1.27
STUB_LEN = 2.54  # Leitungsstummel an belegten Pins (2 Rasterschritte)
COL_WIDTH = 90.0        # mm pro Funktionsblock-Spalte
IC_X_OFF = 30.0
PASSIVE_X_OFF = 62.0
ROW_TOP = 40.0
PASSIVE_STEP = 15.0
IC_STEP = 60.0


def _uid(*parts: str) -> str:
    return str(uuid.uuid5(EXPORT_NS, ":".join(parts)))


def _snap(v: float) -> float:
    return round(round(v / GRID) * GRID, 2)


def write_schematic(model: ExportModel, symbols_dir: Path, project_name: str) -> str:
    sheet_uuid = _uid("sheet", project_name)

    # Symbole einmalig laden/einbetten
    lib_nodes: list = []
    seen: set[str] = set()
    pins_by_libid: dict[str, list[Pin]] = {}

    def embed(lib_id: str) -> None:
        if lib_id in seen:
            return
        seen.add(lib_id)
        libname, symname = lib_id.split(":", 1)
        node = extract_symbol(libname, symname, symbols_dir)
        lib_nodes.append(node)
        pins_by_libid[lib_id] = symbol_pins(node)

    for inst in model.instances:
        embed(inst.lib_id)

    # Netz-Analyse: Anschlusszahl, power_in-Netze, getriebene Netze
    net_counts: Counter[str] = Counter()
    power_in_nets: set[str] = set()
    driven_nets: set[str] = set()
    for inst in model.instances:
        pins = {p.number: p for p in pins_by_libid[inst.lib_id]}
        for pin_no, net in inst.pin_nets.items():
            net_counts[net] += 1
            etype = pins[pin_no].etype if pin_no in pins else "passive"
            if etype == "power_in":
                power_in_nets.add(net)
            elif etype == "power_out":
                driven_nets.add(net)

    single_point = {net for net, cnt in net_counts.items() if cnt == 1}
    flags_needed = sorted((power_in_nets - driven_nets) - single_point)
    if flags_needed:
        embed("power:PWR_FLAG")

    # Platzierung: pro Block eine Spalte; ICs links untereinander, Passive rechts
    blocks_in_order: list[str] = []
    for inst in model.instances:
        if inst.block_name not in blocks_in_order:
            blocks_in_order.append(inst.block_name)

    placed: list[tuple[SymbolInstance, float, float]] = []
    texts: list[str] = []
    max_y = ROW_TOP
    for col, block_name in enumerate(blocks_in_order):
        x_base = 20.0 + col * COL_WIDTH
        texts.append(_text_node(block_name, _snap(x_base + 5), _snap(ROW_TOP - 12)))
        ic_y = ROW_TOP
        passive_y = ROW_TOP
        for inst in model.instances:
            if inst.block_name != block_name:
                continue
            is_passive = inst.lib_id.startswith("Device:") or inst.lib_id.startswith("Diode:")
            if is_passive:
                x, y = x_base + PASSIVE_X_OFF, passive_y
                passive_y += PASSIVE_STEP
            else:
                x, y = x_base + IC_X_OFF, ic_y
                ic_y += IC_STEP
            placed.append((inst, _snap(x), _snap(y)))
            max_y = max(max_y, ic_y, passive_y)

    body_parts: list[str] = []
    label_parts: list[str] = []
    for inst, x, y in placed:
        pins = pins_by_libid[inst.lib_id]
        body_parts.append(_symbol_node(inst, x, y, sheet_uuid, project_name, pins))
        for pin in pins:
            net = inst.pin_nets.get(pin.number)
            px, py, prot = _pin_position(pin, x, y)
            if net and net not in single_point:
                ex, ey = _stub_end(pin, px, py)
                label_parts.append(_wire_node(px, py, ex, ey, inst.ref, pin.number))
                label_parts.append(_label_node(net, ex, ey, prot, inst.ref, pin.number))
            else:
                if net:  # Ein-Punkt-Netz: offen lassen und melden
                    model.warnings.append(
                        f"Netz {net!r} hat nur einen Anschluss ({inst.ref} Pin {pin.number}) "
                        f"— Pin bleibt offen (no_connect)"
                    )
                label_parts.append(
                    f'  (no_connect (at {px} {py}) (uuid "{_uid("nc", inst.ref, pin.number)}"))'
                )

    # PWR_FLAG-Zeile für treiberlose Versorgungsnetze
    flag_y = _snap(max_y + 25)
    for i, net in enumerate(flags_needed):
        fx = _snap(20 + i * 25)
        ref = f"#FLG{i + 1:02d}"
        flag_pins = pins_by_libid["power:PWR_FLAG"]
        flag_inst = SymbolInstance(
            ref=ref, lib_id="power:PWR_FLAG", value=net, footprint="",
            block_name="__power__", pin_nets={flag_pins[0].number: net},
            status="mapped",
        )
        body_parts.append(_symbol_node(flag_inst, fx, flag_y, sheet_uuid, project_name,
                                       flag_pins, in_bom=False))
        px, py, prot = _pin_position(flag_pins[0], fx, flag_y)
        ex, ey = _stub_end(flag_pins[0], px, py)
        label_parts.append(_wire_node(px, py, ex, ey, ref, flag_pins[0].number))
        label_parts.append(_label_node(net, ex, ey, prot, ref, flag_pins[0].number))

    lib_text = "\n    ".join(sexpr.dumps(n, indent=2) for n in lib_nodes)
    parts = [
        '(kicad_sch (version 20250114) (generator "hardware_copilot") (generator_version "9.0")',
        f'  (uuid "{sheet_uuid}")',
        '  (paper "A3")',
        f"  (lib_symbols\n    {lib_text}\n  )",
        *texts,
        *body_parts,
        *label_parts,
        '  (sheet_instances (path "/" (page "1")))',
        ")",
    ]
    return "\n".join(parts) + "\n"


def _pin_position(pin: Pin, x: float, y: float) -> tuple[float, float, int]:
    """Pin-Anschlusspunkt im Blatt (Symbol-Y ist gegenüber Blatt-Y gespiegelt)."""
    px = _snap(x + pin.x)
    py = _snap(y - pin.y)
    rot = pin.rotation % 360
    label_rot = (rot + 180) % 360
    if label_rot in (90, 270):
        label_rot = 360 - label_rot
    return px, py, label_rot


def _stub_end(pin: Pin, px: float, py: float) -> tuple[float, float]:
    """Endpunkt des Leitungsstummels: vom Anschlusspunkt weg vom Symbolkörper.

    Der Pin-Winkel zeigt im Symbol vom Anschlusspunkt zum Körper; im Blatt ist
    die Y-Achse gespiegelt, daher Richtungsvektor (-cos, +sin)."""
    theta = math.radians(pin.rotation % 360)
    dx = -math.cos(theta)
    dy = math.sin(theta)
    return _snap(px + dx * STUB_LEN), _snap(py + dy * STUB_LEN)


def _wire_node(x1: float, y1: float, x2: float, y2: float, ref: str, pin_no: str) -> str:
    return (
        f"  (wire (pts (xy {x1} {y1}) (xy {x2} {y2})) "
        f"(stroke (width 0) (type default)) "
        f'(uuid "{_uid("wire", ref, pin_no)}"))'
    )


def _symbol_node(inst: SymbolInstance, x: float, y: float, sheet_uuid: str,
                 project_name: str, pins: list[Pin], in_bom: bool = True) -> str:
    su = _uid("sym", inst.ref)
    pin_uuids = "\n".join(
        f'    (pin "{num}" (uuid "{_uid("pin", inst.ref, num)}"))'
        for num in sorted({p.number for p in pins})
    )
    props = [
        ("Reference", inst.ref, x + 12, y - 4, ""),
        ("Value", inst.value, x + 12, y - 1.5, ""),
        ("Footprint", inst.footprint, x, y, " hide"),
        ("Datasheet", "~", x, y, " hide"),
    ]
    prop_text = "\n".join(
        f'    (property "{k}" "{_esc(v)}" (at {_snap(px)} {_snap(py)} 0) '
        f"(effects (font (size 1.27 1.27)){hide}))"
        for k, v, px, py, hide in props
    )
    bom = "yes" if in_bom else "no"
    return (
        f'  (symbol (lib_id "{inst.lib_id}") (at {x} {y} 0) (unit 1)\n'
        f"    (in_bom {bom}) (on_board yes) (dnp no)\n"
        f'    (uuid "{su}")\n'
        f"{prop_text}\n"
        f"{pin_uuids}\n"
        f'    (instances (project "{_esc(project_name)}" '
        f'(path "/{sheet_uuid}" (reference "{inst.ref}") (unit 1))))\n'
        f"  )"
    )


def _label_node(net: str, x: float, y: float, rot: int, ref: str, pin_no: str) -> str:
    justify = "left" if rot in (0, 90) else "right"
    return (
        f'  (label "{_esc(net)}" (at {x} {y} {rot}) '
        f"(effects (font (size 1.27 1.27)) (justify {justify})) "
        f'(uuid "{_uid("lbl", ref, pin_no)}"))'
    )


def _text_node(text: str, x: float, y: float) -> str:
    return (
        f'  (text "{_esc(text)}" (exclude_from_sim no) (at {x} {y} 0) '
        f"(effects (font (size 2.54 2.54) bold)) "
        f'(uuid "{_uid("txt", text)}"))'
    )


def _esc(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')
