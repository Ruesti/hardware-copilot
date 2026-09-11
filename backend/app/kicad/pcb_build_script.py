"""Erzeugt eine .kicad_pcb über die offizielle pcbnew-API.

Läuft als Subprozess unter dem System-Python (/usr/bin/python3), weil das
pcbnew-Modul dort vom kicad-Paket installiert wird. Eingabe: JSON auf stdin,
Ausgabepfad als argv[1]. Kein Import aus der App — bewusst eigenständig.

JSON-Schema:
{
  "instances": [{"ref","value","footprint","x","y","pads":{"1":"GND",...}}],
  "texts": [{"text","x","y"}],
  "outline": {"x0","y0","x1","y1"}
}
"""
import json
import sys

import pcbnew

FOOTPRINTS_DIR = "/usr/share/kicad/footprints"


def main() -> int:
    out_path = sys.argv[1]
    data = json.load(sys.stdin)

    board = pcbnew.CreateEmptyBoard()
    # Modul-Footprints (z. B. ESP32-WROOM) nutzen 0,2-mm-Thermal-Vias —
    # Standard bei allen gängigen Fertigern, Board-Default ist strenger.
    board.GetDesignSettings().m_MinThroughDrill = pcbnew.FromMM(0.2)

    nets: dict[str, pcbnew.NETINFO_ITEM] = {}

    def net_for(name: str) -> pcbnew.NETINFO_ITEM:
        if name not in nets:
            item = pcbnew.NETINFO_ITEM(board, name)
            board.Add(item)
            nets[name] = item
        return nets[name]

    skipped = []
    for inst in data["instances"]:
        lib, _, fpname = inst["footprint"].partition(":")
        fp = pcbnew.FootprintLoad(f"{FOOTPRINTS_DIR}/{lib}.pretty", fpname)
        if fp is None:
            skipped.append({"ref": inst["ref"], "footprint": inst["footprint"],
                            "reason": "Footprint nicht ladbar"})
            continue
        fp.SetReference(inst["ref"])
        fp.SetValue(inst["value"])
        fp.SetPosition(pcbnew.VECTOR2I_MM(inst["x"], inst["y"]))
        board.Add(fp)
        pads = inst.get("pads", {})
        for pad in fp.Pads():
            net_name = pads.get(pad.GetNumber())
            if net_name:
                pad.SetNet(net_for(net_name))

    layers = {"silk": pcbnew.F_SilkS, "comments": pcbnew.Cmts_User}
    for t in data.get("texts", []):
        txt = pcbnew.PCB_TEXT(board)
        txt.SetText(t["text"])
        txt.SetPosition(pcbnew.VECTOR2I_MM(t["x"], t["y"]))
        txt.SetLayer(layers.get(t.get("layer", "silk"), pcbnew.F_SilkS))
        if t.get("layer") == "comments":
            txt.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        board.Add(txt)

    o = data.get("outline")
    if o:
        rect = pcbnew.PCB_SHAPE(board)
        rect.SetShape(pcbnew.SHAPE_T_RECT)
        rect.SetStart(pcbnew.VECTOR2I_MM(o["x0"], o["y0"]))
        rect.SetEnd(pcbnew.VECTOR2I_MM(o["x1"], o["y1"]))
        rect.SetLayer(pcbnew.Edge_Cuts)
        rect.SetWidth(pcbnew.FromMM(0.1))
        board.Add(rect)

    pcbnew.SaveBoard(out_path, board)
    print(json.dumps({"skipped": skipped}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
