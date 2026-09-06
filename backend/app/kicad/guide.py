"""Routing-Anleitung: projektspezifische Hinweise + HTML mit Niveau-Umschalter.

Die Hinweise werden deterministisch aus dem Export-Modell abgeleitet
(net_role, Blöcke, Netznamen) — kein LLM-Aufruf.
"""
from __future__ import annotations

import html

from .netlist import ExportModel


def project_hints(model: ExportModel) -> list[str]:
    """Kurze, projektspezifische Routing-Hinweise (auch für den PCB-Kommentar-Layer)."""
    hints: list[str] = []

    # IC je Block (für "nah an ...")
    ic_by_block: dict[str, str] = {}
    for i in model.instances:
        if not i.lib_id.startswith(("Device:", "Diode:", "power:")):
            ic_by_block.setdefault(i.block_name, i.ref)

    decoupling: dict[str, list[str]] = {}
    for i in model.instances:
        role = i.net_role or ""
        kind, _, target = role.partition(":")
        ic = ic_by_block.get(i.block_name, "dem IC")
        if kind == "decoupling":
            decoupling.setdefault(ic, []).append(i.ref)
        elif kind == "prog_resistor":
            hints.append(f"{i.ref} (PROG) direkt neben {ic} platzieren — kurze Leitung zu Pin PROG.")
        elif kind == "protect":
            hints.append(f"{i.ref} (ESD-Schutz, {target}) nah an die Buchse, VOR den Chip.")
        elif kind == "pulldown" and target in ("CC1", "CC2"):
            hints.append(f"{i.ref} ({target}-Widerstand) dicht an den USB-C-Stecker.")
        elif kind == "series":
            hints.append(f"{i.ref} (Serienwiderstand {target}) nah an die Signalquelle setzen.")

    for ic, refs in decoupling.items():
        hints.insert(0, f"{', '.join(sorted(refs))} (Entkopplung) so nah wie möglich "
                        f"an die Versorgungspins von {ic}.")

    nets = {n for i in model.instances for n in i.pin_nets.values()}
    if {"USB_DP", "USB_DN"} <= nets:
        hints.append("USB_DP/USB_DN als Paar führen: gleiche Länge, direkt nebeneinander, "
                     "keine Unterbrechungen der Massefläche darunter.")
    if "GND" in nets:
        hints.append("GND als Massefläche auf der Unterseite (B.Cu) ausführen statt einzelner Leitungen.")
    hints.append("Leiterbahnen mit 45°-Knicken führen, keine 90°-Ecken.")
    hints.append("Versorgung (VBUS/VBAT/3V3) breiter routen (0,5–0,8 mm), Signale 0,2–0,3 mm.")
    return hints


def build_guide_html(model: ExportModel, project_name: str) -> str:
    items = "".join(f"<li>{html.escape(h)}</li>" for h in project_hints(model))
    name = html.escape(project_name)
    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<title>Routing-Anleitung – {name}</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 780px; margin: 2rem auto;
         padding: 0 1rem; line-height: 1.55; color: #1a1a1a; }}
  h1 {{ font-size: 1.4rem; }} h2 {{ font-size: 1.1rem; margin-top: 1.6rem; }}
  .toggle {{ position: sticky; top: 0; background: #fff; padding: .6rem 0;
             border-bottom: 1px solid #ddd; }}
  .toggle button {{ padding: .4rem 1rem; border: 1px solid #bbb; background: #f5f5f5;
                    border-radius: 8px; cursor: pointer; font-size: .9rem; }}
  .toggle button.active {{ background: #16a34a; color: #fff; border-color: #16a34a; }}
  body.beginner .pro {{ display: none; }}
  body.pro .beginner {{ display: none; }}
  li {{ margin: .35rem 0; }}
  kbd {{ background: #eee; border-radius: 4px; padding: 0 .35rem; font-size: .85em; }}
</style></head>
<body class="beginner">
<div class="toggle">
  Niveau:
  <button id="b1" class="active" onclick="setLevel('beginner')">Einsteiger</button>
  <button id="b2" onclick="setLevel('pro')">Fortgeschritten</button>
</div>
<h1>Routing-Anleitung: {name}</h1>

<h2>Hinweise zu diesem Projekt</h2>
<ul>{items}</ul>

<div class="beginner">
<h2>KiCad-Grundlagen (Einsteiger)</h2>
<ul>
<li>Öffne den <b>PCB-Editor</b> (Platinensymbol im KiCad-Projektfenster). Die dünnen
    Gummiband-Linien („Ratsnest") zeigen, welche Anschlüsse verbunden werden müssen.</li>
<li>Route eine Verbindung mit <kbd>X</kbd>: Pad anklicken, der Linie folgen, am Ziel-Pad
    klicken. Abbrechen mit <kbd>Esc</kbd>.</li>
<li>Mit <kbd>V</kbd> setzt du beim Routen eine Durchkontaktierung (Via) und wechselst
    auf die Unterseite (B.Cu), z. B. um eine andere Leitung zu kreuzen.</li>
<li>Bauteile verschieben: <kbd>M</kbd>, drehen: <kbd>R</kbd>. Die Blockgruppen darfst
    du frei umsortieren — die Gummibänder wandern mit.</li>
<li>Reihenfolge: erst GND und Versorgung (dicke Bahnen), dann die Signale.</li>
<li>Am Ende <b>Prüfung → Design Rules Checker (DRC)</b> laufen lassen — 0 Fehler
    und 0 unverbundene Netze ist das Ziel.</li>
</ul>
</div>

<div class="pro">
<h2>Richtwerte (Fortgeschritten)</h2>
<ul>
<li>Leiterbreiten: Signale 0,2–0,3 mm; Versorgung 0,5–0,8 mm; Ladepfad VBUS→VBAT
    nach Strom dimensionieren (500 mA → ≥0,5 mm bei 35 µm Kupfer).</li>
<li>USB 2.0: differenzielles Paar ~90 Ω, Längen matchen (±1 mm reicht bei Full-Speed),
    durchgehende GND-Referenzfläche unter dem Paar.</li>
<li>Entkopplung: kleinster Kondensator am nächsten zum Pin; Via zur Massefläche
    direkt am Pad, nicht am Ende einer Stichleitung.</li>
<li>Massefläche auf B.Cu; Rückstrompfade beachten — keine Schlitze unter
    schnellen Signalen.</li>
<li>Thermik: Exposed Pads (SHT31) mit Thermal-Vias anbinden; LDO-GND großzügig.</li>
<li>ESD-Dioden in Reihe zur Buchse anordnen: Buchse → Diode → Serienelement → Chip.</li>
</ul>
</div>

<script>
function setLevel(l) {{
  document.body.className = l;
  document.getElementById('b1').classList.toggle('active', l === 'beginner');
  document.getElementById('b2').classList.toggle('active', l === 'pro');
}}
</script>
</body></html>
"""
