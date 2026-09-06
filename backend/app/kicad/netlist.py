"""Deterministische Netz-Ableitung: DB-Design + Bibliothek → Export-Modell.

Arbeitsteilung (Spec 2026-09-06): Die KI liefert Netz-Semantik (conn_type,
net_role), die Bibliothek liefert Pin-Fakten (role_to_pin) — hier wird beides
deterministisch zu einer Pin→Netz-Zuordnung kombiniert. Kein LLM-Aufruf.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .library import Library

REF_PREFIX = {
    "mcu": "U", "power_ic": "U", "sensor": "U", "memory": "U", "other": "U",
    "diode": "D", "protection": "D", "transistor": "Q",
    "passive_resistor": "R", "passive_capacitor": "C", "passive_inductor": "L",
    "connector": "J", "crystal": "Y",
}

# conn_type → Netznamen, die diese Verbindung zwischen zwei Blöcken aufspannt
CONN_TYPE_NETS = {
    "gnd": ["GND"],
    "i2c": ["SDA", "SCL"],
    "spi": ["SPI_CLK", "SPI_MOSI", "SPI_MISO", "SPI_CS"],
    "usb": ["USB_DP", "USB_DN"],
}

# Rollen, die 1:1 an ein gleichnamiges Blocknetz gehen (wenn vorhanden)
INTERFACE_ROLES = [
    "SDA", "SCL", "SPI_CLK", "SPI_MOSI", "SPI_MISO", "SPI_CS",
    "USB_DP", "USB_DN", "VBUS", "VBAT", "STAT", "PROG", "CC1", "CC2",
    "EN", "BOOT",
]


@dataclass
class SymbolInstance:
    ref: str
    lib_id: str
    value: str
    footprint: str
    block_name: str
    pin_nets: dict[str, str]
    status: str  # "mapped" | "fallback" | "unverified"
    name: str = ""
    component_id: str = ""


@dataclass
class ExportModel:
    instances: list[SymbolInstance] = field(default_factory=list)
    unmapped: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def normalize_power_net(label: str) -> str:
    """'3.3V' → '3V3'; 'VBUS 5V' → 'VBUS'; 'VBAT 3.6-4.2V' → 'VBAT'; '12V' → '12V'."""
    label = (label or "").strip()
    for name in ("VBUS", "VBAT", "VCC", "VDD", "VIN", "VOUT"):
        if label.upper().startswith(name):
            return name
    m = re.match(r"^(\d+)[.,](\d+)\s*V", label, re.IGNORECASE)
    if m:
        return f"{m.group(1)}V{m.group(2)}"
    m = re.match(r"^(\d+)\s*V", label, re.IGNORECASE)
    if m:
        return f"{m.group(1)}V"
    return label.replace(" ", "_").upper() or "PWR"


def _detect_usb_signal(label: str) -> bool:
    text = (label or "").upper()
    return "USB" in text or ("D+" in text and "D-" in text)


def build_export_model(blocks, connections, components, library: Library) -> ExportModel:
    model = ExportModel()
    block_by_id = {b.id: b for b in blocks}

    # 1) Blocknetze aus Verbindungen
    block_nets: dict[str, set[str]] = {b.id: set() for b in blocks}
    supply_net: dict[str, str] = {}
    for conn in connections:
        src, tgt = conn.source_block_id, conn.target_block_id
        if src not in block_by_id or tgt not in block_by_id:
            continue
        ctype = (conn.conn_type or "signal").lower()
        if ctype in CONN_TYPE_NETS:
            nets = CONN_TYPE_NETS[ctype]
        elif ctype == "power":
            net = normalize_power_net(conn.label)
            nets = [net]
            # Versorgungsnetz des Zielblocks (Quelle ist der Versorger)
            supply_net.setdefault(tgt, net)
        elif ctype == "signal" and _detect_usb_signal(conn.label):
            nets = ["USB_DP", "USB_DN"]
        else:
            continue  # generische Signale ohne ableitbare Netznamen
        for net in nets:
            block_nets[src].add(net)
            block_nets[tgt].add(net)

    # 3V3-Heuristik: Blöcke ohne eingehendes power, aber mit GND-Anbindung,
    # bekommen kein Versorgungsnetz — bewusst offen lassen.

    # 2) Referenzen deterministisch vergeben (Block-Reihenfolge, dann Komponenten-Reihenfolge)
    counters: dict[str, int] = {}
    block_order = {b.id: i for i, b in enumerate(blocks)}
    comps = sorted(
        components,
        key=lambda c: (block_order.get(c.block_id, 999), getattr(c, "id", "")),
    )

    for comp in comps:
        block = block_by_id.get(comp.block_id)
        block_name = block.name if block else "(ohne Block)"
        part = library.for_component(comp.mpn, comp.type)
        if part is None:
            model.unmapped.append({
                "name": comp.name, "mpn": comp.mpn, "type": comp.type,
                "block_name": block_name, "reason": "kein Bibliothekseintrag",
            })
            continue

        prefix = REF_PREFIX.get(comp.type or "other", "U")
        counters[prefix] = counters.get(prefix, 0) + 1
        ref = f"{prefix}{counters[prefix]}"
        nets_here = block_nets.get(comp.block_id, set()) if comp.block_id else set()
        supply = supply_net.get(comp.block_id, "")

        pin_nets: dict[str, str] = {}
        if comp.net_role:
            pin_nets = _passive_nets(comp.net_role, part, supply, nets_here, model, ref)
        else:
            for role, numbers in part.role_to_pin.items():
                net = _net_for_role(role, supply, nets_here)
                if net:
                    for n in numbers:
                        pin_nets[n] = net
            if not part.role_to_pin or (not pin_nets and part.role_to_pin.keys() <= {"P1", "P2"}):
                model.warnings.append(
                    f"{ref} ({comp.name}, {block_name}): keine net_role und keine "
                    f"ableitbaren Rollen — Pins bleiben offen"
                )

        model.instances.append(SymbolInstance(
            ref=ref, lib_id=part.lib_id,
            value=comp.value or comp.name or "",
            footprint=part.footprint or (getattr(comp, "package", "") or ""),
            block_name=block_name, pin_nets=pin_nets,
            status="mapped" if not library.is_fallback(comp.mpn) else "fallback",
            name=comp.name or "", component_id=getattr(comp, "id", ""),
        ))
    return model


def _net_for_role(role: str, supply: str, nets_here: set[str]) -> str | None:
    if role == "GND" and "GND" in nets_here:
        return "GND"
    if role == "VDD":
        return supply or None
    if role == "VIN":
        return supply or None
    if role == "VOUT":
        # Ausgangsnetz eines Reglers: das power-Netz, das dieser Block treibt —
        # als Blocknetz vorhanden, aber nicht sein eigenes supply
        cands = [n for n in nets_here if n not in {"GND", supply} and _looks_like_power(n)]
        return cands[0] if len(cands) == 1 else None
    if role in INTERFACE_ROLES and role in nets_here:
        return role
    if role == "EN":
        # Enable ohne eigenes Netz: aktiv — an die Versorgung des Blocks
        return supply or None
    return None


def _looks_like_power(net: str) -> bool:
    return bool(re.match(r"^(\d+V\d*|V[A-Z]+)$", net))


def _passive_nets(net_role: str, part, supply: str, nets_here: set[str],
                  model: ExportModel, ref: str) -> dict[str, str]:
    p1 = part.role_to_pin.get("P1", ["1"])
    p2 = part.role_to_pin.get("P2", ["2"])

    def both(a: str | None, b: str | None) -> dict[str, str]:
        out: dict[str, str] = {}
        if a:
            for n in p1:
                out[n] = a
        if b:
            for n in p2:
                out[n] = b
        return out

    kind, _, target = net_role.partition(":")
    if kind == "decoupling":
        if not supply:
            model.warnings.append(f"{ref}: decoupling ohne Versorgungsnetz am Block")
        return both(supply or None, "GND")
    if kind == "pullup":
        return both(target or None, supply or None)
    if kind in ("pulldown", "protect"):
        return both(target or None, "GND")
    if kind == "series":
        # Vereinfachung 5.1: Serien-Element trennt Netz in <NETZ> / <NETZ>_S
        return both(target or None, f"{target}_S" if target else None)
    if kind == "prog_resistor":
        return both("PROG", "GND")
    model.warnings.append(f"{ref}: unbekannte net_role {net_role!r} — Pins offen")
    return {}
